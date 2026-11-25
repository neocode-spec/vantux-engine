const { createClient } = require("@supabase/supabase-js");

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { action, username, threadId, title, messages, chatId, fact, memoryId } = req.body || {};

  try {
    if (action === "load_all") {
      const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

      const [chatsRes, memRes, usageRes] = await Promise.all([
        supabase
          .from("vantux_chats")
          .select("*")
          .eq("username", username)
          .order("created_at", { ascending: false }),
        supabase
          .from("vantux_memory")
          .select("*")
          .eq("username", username)
          .order("created_at", { ascending: true }),
        supabase
          .from("vantux_usage_log")
          .select("id")
          .eq("username", username)
          .gte("created_at", cutoff),
      ]);

      return res.json({
        threads: chatsRes.data || [],
        memories: memRes.data || [],
        usageCount: (usageRes.data || []).length,
      });
    }

    if (action === "save_thread") {
      const responseJson = JSON.stringify(messages);
      if (threadId) {
        await supabase
          .from("vantux_chats")
          .update({ scenario: title, response: responseJson })
          .eq("id", threadId);
        return res.json({ id: threadId });
      } else {
        const { data } = await supabase
          .from("vantux_chats")
          .insert({ username, scenario: title, response: responseJson })
          .select();
        return res.json({ id: data && data[0] ? data[0].id : null });
      }
    }

    if (action === "delete_thread") {
      await supabase.from("vantux_chats").delete().eq("id", chatId);
      return res.json({ ok: true });
    }

    if (action === "add_memory") {
      const { data } = await supabase
        .from("vantux_memory")
        .insert({ username, fact })
        .select();
      return res.json({ memory: data && data[0] ? data[0] : null });
    }

    if (action === "delete_memory") {
      await supabase.from("vantux_memory").delete().eq("id", memoryId);
      return res.json({ ok: true });
    }

    return res.status(400).json({ error: "Invalid action" });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
};
