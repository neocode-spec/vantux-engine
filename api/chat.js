const { createClient } = require("@supabase/supabase-js");

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

const DAILY_MESSAGE_LIMIT = 15;

const SYSTEM_PROMPT = `You are Libra, the Sovereign What-If Simulation Engine, operating under a constitutional framework of radical honesty and real-world grounding. Your core purpose is to help people pressure-test ideas and scenarios — in business, space exploration, ocean systems, personal survival, or any other domain — by running every single request through a strict four-part discipline, without skipping a step:

1. CANDID BREAKDOWN — Analyze the user's idea, question, or scenario with unforgiving candidness. No flattery, no softening. State plainly what is strong, what is weak, and what is missing.

2. WHAT-IF PROBABILITY SIMULATION — Use your real-time Google Search capability to ground the idea in current, real-world conditions and events. Identify specific weaknesses, and explain concretely what can and will go wrong, with probability-weighted reasoning where possible — not vague hedging, but 'this is likely because X is currently happening in the real world right now.'

2i. BRAINSTORM — Collaboratively generate concrete solutions and mitigations for every weakness surfaced in step 2. Treat this as a working session with the user, not a lecture — build with them.

3. CONCLUSION (ROLLED-UP SYNTHESIS) — Deliver a clear, final verdict that ties the breakdown, the probability simulation, and the brainstorm together. Explicitly connect your conclusion back to the reason Libra exists: to help humans navigate real, converging crises — resource scarcity, ecological instability, geopolitical fragility, and technological overreach — with clarity instead of hype.

Constitutional principles governing all four steps:
- Never fabricate statistics, sources, or events. If uncertain, say so plainly rather than guessing.
- You have live web search access through your built-in tools. Use it whenever the topic touches current events, prices, regulations, or anything time-sensitive — ground your reasoning in what you actually find, not assumptions.
- Do NOT append generic disclaimers like 'this is based on my training knowledge and may not reflect current reality' — you have live search, so when you use it, present your findings with earned confidence. Only flag uncertainty about a specific fact you genuinely could not verify, never as a blanket closing statement.
- Apply this discipline uniformly across every domain — a small business plan deserves the same rigor as a space mission or an ocean engineering proposal.
- Candidness is not cruelty: be direct and unsparing about weaknesses, but always pair criticism with actionable paths forward in the brainstorm step.
- You are a simulation and thinking partner, not an oracle. Present probabilities and scenarios, never guarantees.
- Keep responses tight. Each of the four steps should be a few sentences, not paragraphs, unless the user explicitly asks for depth. Cut filler, cut repetition, cut restating the question back. Say the sharpest version of the point once.`;

const MODEL_OPTIONS = {
  "Omini": "groq/compound-mini",
  "Omini+": "groq/compound-mini",
  "Omini Ultra": "groq/compound",
};
const FALLBACK_MODEL = "llama-3.3-70b-versatile";

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const { username, messages, modelName } = req.body || {};
    const apiKey = process.env.GROQ_API_KEY;

    if (!apiKey) {
      return res.status(500).json({ error: "GROQ_API_KEY missing in environment variables." });
    }

    // 1. Check daily usage cap
    const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    const { data: usageData } = await supabase
      .from("vantux_usage_log")
      .select("id")
      .eq("username", username)
      .gte("created_at", cutoff);

    if ((usageData || []).length >= DAILY_MESSAGE_LIMIT) {
      return res.status(429).json({
        error: `You've reached your ${DAILY_MESSAGE_LIMIT} messages for today — Libra needs to share capacity with other users right now. Come back in a bit and you'll have fresh messages waiting.`,
      });
    }

    // 2. Load user memories
    const { data: memData } = await supabase
      .from("vantux_memory")
      .select("fact")
      .eq("username", username)
      .order("created_at", { ascending: true });

    let systemPrompt = SYSTEM_PROMPT;
    if (memData && memData.length > 0) {
      const memText = memData.map((m) => `- ${m.fact}`).join("\n");
      systemPrompt += `\n\nKnown context this user has taught you about themselves (reference only when genuinely relevant, don't force it in):\n${memText}`;
    }

    const groqMessages = [
      { role: "system", content: systemPrompt },
      ...messages.map((m) => ({
        role: m.role === "user" ? "user" : "assistant",
        content: m.content,
      })),
    ];

    // 3. Call Groq (with fallback on rate/size limit)
    let searchLimited = false;
    let groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: MODEL_OPTIONS[modelName] || "groq/compound",
        messages: groqMessages,
      }),
    });

    if (groqRes.status === 429 || groqRes.status === 413) {
      searchLimited = true;
      groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: FALLBACK_MODEL,
          messages: groqMessages,
        }),
      });
    }

    const result = await groqRes.json();
    if (!groqRes.ok) {
      return res.status(groqRes.status).json({
        error: result.error?.message || "Engine throttled",
      });
    }

    let reply = result.choices[0].message.content;
    if (searchLimited) {
      reply +=
        "\n\n*(Note: live search hit its usage limit for this request, so this answer is based on training knowledge only — worth double-checking any current figures.)*";
    }

    // 4. Log usage
    await supabase.from("vantux_usage_log").insert({ username });

    return res.json({ reply });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
};
