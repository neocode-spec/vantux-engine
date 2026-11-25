const { createClient } = require("@supabase/supabase-js");
const bcrypt = require("bcryptjs");
const crypto = require("crypto");

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { action, username, password, fullName, token } = req.body || {};

  try {
    if (action === "login") {
      const { data, error } = await supabase
        .from("vantux_users")
        .select("*")
        .eq("username", username);

      if (error || !data || data.length === 0) {
        return res.json({ status: false, message: "Username/password is incorrect" });
      }

      const user = data[0];
      const stored = user.password || "";
      let valid = false;

      if (stored.startsWith("$2")) {
        valid = await bcrypt.compare(password, stored);
      } else if (stored === password) {
        valid = true;
        const newHash = await bcrypt.hash(password, 10);
        await supabase
          .from("vantux_users")
          .update({ password: newHash })
          .eq("username", username);
      }

      if (!valid) {
        return res.json({ status: false, message: "Username/password is incorrect" });
      }

      const newToken = crypto.randomUUID();
      await supabase
        .from("vantux_users")
        .update({ session_token: newToken })
        .eq("username", username);

      return res.json({
        status: true,
        name: user.full_name,
        username: user.username,
        token: newToken,
      });
    }

    if (action === "register") {
      const { data: exists } = await supabase
        .from("vantux_users")
        .select("username")
        .eq("username", username);

      if (exists && exists.length > 0) {
        return res.json({ status: false, message: "Username already exists!" });
      }

      const hashedPassword = await bcrypt.hash(password, 10);
      const { error } = await supabase.from("vantux_users").insert({
        username,
        full_name: fullName,
        password: hashedPassword,
        is_premium: true,
      });

      if (error) {
        return res.json({ status: false, message: `Registration failed: ${error.message}` });
      }

      return res.json({
        status: true,
        message: "Account created successfully! Switch to 'Login' to enter.",
      });
    }

    if (action === "validate") {
      if (!token) return res.json({ status: false });
      const { data } = await supabase
        .from("vantux_users")
        .select("*")
        .eq("session_token", token);

      if (data && data.length > 0) {
        return res.json({
          status: true,
          name: data[0].full_name,
          username: data[0].username,
        });
      }
      return res.json({ status: false });
    }

    if (action === "logout") {
      if (username) {
        await supabase
          .from("vantux_users")
          .update({ session_token: null })
          .eq("username", username);
      }
      return res.json({ status: true });
    }

    return res.status(400).json({ error: "Invalid action" });
  } catch (err) {
    return res.status(500).json({ status: false, message: err.message });
  }
};
