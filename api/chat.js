const { createClient } = require("@supabase/supabase-js");
const { GoogleGenAI } = require("@google/genai");

const DAILY_MESSAGE_LIMIT = 15;

const SYSTEM_PROMPT = `You are Libra, the Sovereign What-If Simulation Engine, operating under a constitutional framework of radical honesty and real-world grounding. Your core purpose is to help people pressure-test ideas and scenarios — in business, space exploration, ocean systems, personal survival, or any other domain — by running every single request through a strict four-part discipline, without skipping a step:

1. CANDID BREAKDOWN — Analyze the user's idea, question, or scenario with unforgiving candidness. No flattery, no softening. State plainly what is strong, what is weak, and what is missing.

2. WHAT-IF PROBABILITY SIMULATION — Use your real-time search capability to ground the idea in current, real-world conditions and events. Identify specific weaknesses, and explain concretely what can and will go wrong, with probability-weighted reasoning where possible.

2i. BRAINSTORM — Collaboratively generate concrete solutions and mitigations for every weakness surfaced in step 2. Treat this as a working session with the user, not a lecture — build with them.

3. CONCLUSION (ROLLED-UP SYNTHESIS) — Deliver a clear, final verdict that ties the breakdown, the probability simulation, and the brainstorm together. Explicitly connect your conclusion back to the reason Libra exists: to help humans navigate real, converging crises with clarity instead of hype.

Constitutional principles:
- Never fabricate statistics, sources, or events. If uncertain, say so plainly rather than guessing.
- You have live web search access through your built-in tools. Use it whenever the topic touches current events, prices, regulations, or anything time-sensitive — ground your reasoning in what you actually find, not assumptions.
- Do NOT append generic disclaimers like 'this is based on my training knowledge and may not reflect current reality' — only flag uncertainty about a specific fact you genuinely could not verify.
- Candidness is not cruelty: be direct and unsparing about weaknesses, but always pair criticism with actionable paths forward in the brainstorm step.
- Keep responses tight. Each of the four steps should be a few sentences unless the user explicitly asks for depth.`;

const GROQ_MODELS = {
  "Omini+": "openai/gpt-oss-120b",
  "Omini Ultra": "groq/compound",
};
const FALLBACK_MODEL = "openai/gpt-oss-120b";

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_KEY) {
      return res.status(500).json({ error: "SUPABASE_URL or SUPABASE_KEY missing in Vercel Environment Variables." });
    }

    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_KEY
    );

    let body = req.body || {};
    if (typeof body === "string") {
      try { body = JSON.parse(body); } catch { body = {}; }
    }

    const { username, messages, modelName } = body;

    // 1. Check daily usage cap
    const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    const { data: usageData } = await supabase
      .from("vantux_usage_log")
      .select("id")
      .eq("username", username)
      .gte("created_at", cutoff);

    if ((usageData || []).length >= DAILY_MESSAGE_LIMIT) {
      return res.status(429).json({
        error: `You've reached your ${DAILY_MESSAGE_LIMIT} messages for today — Libra needs to share capacity with other users right now.`,
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

    let reply = "";

    // 3A. OMINI -> GEMINI API (gemini-4-hydrogen + Google Search)
    if (modelName === "Omini") {
      const geminiKey = process.env.GEMINI_API_KEY || process.env.GEMINI_KEY;
      if (!geminiKey) {
        return res.status(500).json({ error: "GEMINI_KEY / GEMINI_API_KEY missing in Vercel Environment Variables." });
      }

      const ai = new GoogleGenAI({ apiKey: geminiKey });

      const formattedInput = (messages || []).map((m) => ({
        role: m.role === "user" ? "user" : "model",
        content: m.content,
      }));

      const interaction = await ai.interactions.create({
        model: "gemini-4-hydrogen",
        system_instruction: systemPrompt,
        input: formattedInput,
        tools: [{ type: "google_search" }],
        store: false,
      });

      reply = interaction.output_text || "No response generated.";
    }
    // 3B. OMINI+ / OMINI ULTRA -> GROQ API (with live web search)
    else {
      const groqKey = process.env.GROQ_API_KEY;
      if (!groqKey) {
        return res.status(500).json({ error: "GROQ_API_KEY missing in Vercel Environment Variables." });
      }

      const selectedModel = GROQ_MODELS[modelName] || "groq/compound";
      const groqMessages = [
        { role: "system", content: systemPrompt },
        ...(messages || []).map((m) => ({
          role: m.role === "user" ? "user" : "assistant",
          content: m.content,
        })),
      ];

      const buildPayload = (model) => {
        const payload = { model, messages: groqMessages };
        if (model === "openai/gpt-oss-120b") {
          payload.tools = [{ type: "browser_search" }];
          payload.tool_choice = "auto";
        }
        return payload;
      };

      let searchLimited = false;
      let groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${groqKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(buildPayload(selectedModel)),
      });

      if (groqRes.status === 429 || groqRes.status === 413) {
        searchLimited = true;
        groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${groqKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(buildPayload(FALLBACK_MODEL)),
        });
      }

      const result = await groqRes.json();
      if (!groqRes.ok) {
        return res.status(groqRes.status).json({
          error: result.error?.message || "Engine throttled",
        });
      }

      reply = result.choices[0].message.content || "";
      if (searchLimited) {
        reply +=
          "\n\n*(Note: live search hit its usage limit for this request, so this answer is based on training knowledge only — worth double-checking any current figures.)*";
      }
    }

    // Clean up raw citation markers if any
    reply = reply.replace(/【[^】]*】/g, "").replace(/ {2,}/g, " ");

    // 4. Log usage
    await supabase.from("vantux_usage_log").insert({ username });

    return res.json({ reply });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
};
