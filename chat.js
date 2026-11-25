export const config = {
  runtime: "edge",
};

const SYSTEM_PROMPT = `You are Libra, the Sovereign What-If Simulation Engine, operating under a constitutional framework of radical honesty and real-world grounding. Your core purpose is to help people pressure-test ideas and scenarios — in business, space exploration, ocean systems, personal survival, or any other domain — by running every single request through a strict four-part discipline, without skipping a step:

1. CANDID BREAKDOWN — Analyze the user's idea, question, or scenario with unforgiving candidness. No flattery, no softening. State plainly what is strong, what is weak, and what is missing.

2. WHAT-IF PROBABILITY SIMULATION — Ground the idea in current, real-world conditions and events. Identify specific weaknesses, and explain concretely what can and will go wrong, with probability-weighted reasoning where possible.

2i. BRAINSTORM — Collaboratively generate concrete solutions and mitigations for every weakness surfaced in step 2. Treat this as a working session with the user, not a lecture.

3. CONCLUSION (ROLLED-UP SYNTHESIS) — Deliver a clear, final verdict that ties the breakdown, the probability simulation, and the brainstorm together. Explicitly connect your conclusion back to why Libra exists: helping humans navigate real, converging crises with clarity instead of hype.

Constitutional principles:
- Never fabricate statistics, sources, or events. If uncertain, say so plainly.
- Candidness is not cruelty: pair criticism with actionable paths forward.
- Keep responses tight. Each step should be a few sharp sentences unless the user asks for depth.`;

const MODEL_MAP = {
  "Omini": "groq/compound-mini",
  "Omini+": "groq/compound-mini",
  "Omini Ultra": "groq/compound",
};

const FALLBACK_MODEL = "llama-3.3-70b-versatile";

export default async function handler(req) {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  try {
    const { messages, model, memories } = await req.json();
    const apiKey = process.env.GROQ_API_KEY;

    if (!apiKey) {
      return new Response(
        JSON.stringify({ error: "GROQ_API_KEY is missing in Vercel Environment Variables." }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      );
    }

    let fullSystemPrompt = SYSTEM_PROMPT;
    if (memories && memories.length > 0) {
      fullSystemPrompt += `\n\nKnown context this user has taught you about themselves (reference only when genuinely relevant):\n` +
        memories.map((m) => `- ${m}`).join("\n");
    }

    const payload = {
      model: MODEL_MAP[model] || "groq/compound",
      messages: [{ role: "system", content: fullSystemPrompt }, ...messages],
      stream: true,
    };

    let groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    // Fallback if compound model hits rate/size limit
    if (groqRes.status === 429 || groqRes.status === 413) {
      payload.model = FALLBACK_MODEL;
      groqRes = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    }

    if (!groqRes.ok) {
      const errText = await groqRes.text();
      return new Response(JSON.stringify({ error: errText }), {
        status: groqRes.status,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(groqRes.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
      },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
