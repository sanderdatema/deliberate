// Deliberators — Live Viewer
// Polls for sessions created by CLI/Claude Code and auto-connects
(function () {
  const connectSection = document.getElementById("connect-section");
  const sessionInput = document.getElementById("session-id");
  const connectBtn = document.getElementById("connect-btn");
  const status = document.getElementById("status");
  const panelsSection = document.getElementById("panels-section");
  const roundLabel = document.getElementById("round-label");
  const agentPanels = document.getElementById("agent-panels");
  const resultSection = document.getElementById("result-section");
  const samenvatterOutput = document.getElementById("samenvatter-output");
  const fullReport = document.getElementById("full-report");

  let ws = null;
  let currentSessionId = null;
  let pollTimer = null;
  const panels = {};

  // Start polling for sessions
  startPolling();

  connectBtn.addEventListener("click", () => {
    const id = sessionInput.value.trim();
    if (id) connectToSession(id);
  });

  function startPolling() {
    setStatus("Wacht op deliberatie... Start /deliberate --web in Claude Code", "");
    pollForSession();
  }

  async function pollForSession() {
    try {
      const res = await fetch("/api/latest-session");
      const { id } = await res.json();

      if (id && id !== currentSessionId) {
        // New session detected — connect!
        currentSessionId = id;
        sessionInput.value = id;
        connectToSession(id);
        return; // Stop polling, WebSocket onclose will restart
      }
    } catch (err) {
      // Server not reachable, keep polling
    }

    // Poll again in 1 second
    pollTimer = setTimeout(pollForSession, 1000);
  }

  function connectToSession(id) {
    // Stop polling while connected
    if (pollTimer) {
      clearTimeout(pollTimer);
      pollTimer = null;
    }

    if (ws) ws.close();

    // Reset UI
    connectSection.classList.add("hidden");
    panelsSection.classList.remove("hidden");
    agentPanels.innerHTML = "";
    Object.keys(panels).forEach((k) => delete panels[k]);
    resultSection.classList.add("hidden");

    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${protocol}//${location.host}/ws/${id}`);

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      handleMessage(msg);
    };

    ws.onclose = () => {
      // Session ended — resume polling for next deliberation
      setTimeout(() => {
        connectSection.classList.remove("hidden");
        setStatus("Klaar voor volgende deliberatie...", "done");
        startPolling();
      }, 2000);
    };

    ws.onerror = () => {
      setStatus("WebSocket fout", "error");
    };

    setStatus(`Verbonden met sessie ${id}`, "running");
  }

  function handleMessage(msg) {
    switch (msg.type) {
      case "deliberation_started":
        setStatus("Deliberatie gestart", "running");
        break;

      case "round_started":
        roundLabel.textContent = `Ronde ${msg.round_number}`;
        roundLabel.className = "round-label active";
        setStatus(`Ronde ${msg.round_number} — analisten denken...`, "running");
        break;

      case "agent_started":
        createPanel(msg.agent_name, msg.round_number);
        break;

      case "text_delta":
        appendText(msg.agent_name, msg.text);
        break;

      case "agent_completed":
        markPanelDone(msg.agent_name);
        break;

      case "round_completed":
        setStatus(`Ronde ${msg.round_number} compleet`, "running");
        break;

      case "editorial_started":
        roundLabel.textContent = "Redactie";
        roundLabel.className = "round-label editorial";
        setStatus("Redactionele fase...", "running");
        break;

      case "editorial_completed":
        setStatus("Redactie compleet", "running");
        break;

      case "result":
        showResult(msg.markdown);
        break;

      case "deliberation_completed":
        setStatus("Deliberatie afgerond", "done");
        break;

      case "error":
        setStatus("Fout: " + msg.message, "error");
        break;
    }
  }

  function createPanel(agentName, roundNumber) {
    const panel = document.createElement("div");
    panel.className = "agent-panel";
    panel.innerHTML = `
      <div class="panel-header">
        <span class="agent-name">${agentName}</span>
        ${roundNumber ? `<span class="round-badge">R${roundNumber}</span>` : ""}
        <span class="panel-status thinking"></span>
      </div>
      <div class="panel-content"></div>
    `;
    agentPanels.appendChild(panel);
    panels[agentName] = panel;
    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function appendText(agentName, text) {
    const panel = panels[agentName];
    if (!panel) return;
    const content = panel.querySelector(".panel-content");
    content.textContent += text;
    content.scrollTop = content.scrollHeight;
  }

  function markPanelDone(agentName) {
    const panel = panels[agentName];
    if (!panel) return;
    panel.classList.add("done");
    const dot = panel.querySelector(".panel-status");
    if (dot) {
      dot.classList.remove("thinking");
      dot.classList.add("complete");
    }
  }

  function showResult(markdown) {
    resultSection.classList.remove("hidden");
    const parts = markdown.split("# Deliberatie:");
    if (parts.length >= 2) {
      samenvatterOutput.textContent = parts[0]
        .replace("## Kort & Concreet", "")
        .replace("---", "")
        .trim();
      fullReport.textContent = "# Deliberatie:" + parts[1];
    } else {
      fullReport.textContent = markdown;
    }
    resultSection.scrollIntoView({ behavior: "smooth" });
  }

  function setStatus(text, state) {
    status.textContent = text;
    status.className = "status " + (state || "");
  }
})();
