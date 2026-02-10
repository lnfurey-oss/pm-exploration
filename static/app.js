const apiBase = "";

const decisionForm = document.getElementById("decision-form");
const assumptionForm = document.getElementById("assumption-form");
const outcomeForm = document.getElementById("outcome-form");
const reflectionForm = document.getElementById("reflection-form");
const reflectionOutput = document.getElementById("reflection-output");

const setOutput = (payload) => {
  reflectionOutput.textContent = JSON.stringify(payload, null, 2);
};

const handleError = (error) => {
  setOutput({ error: error.message || "Something went wrong" });
};

decisionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(decisionForm);
  const constraintsRaw = formData.get("constraints");
  const constraints = constraintsRaw
    ? constraintsRaw
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
        .map((text) => ({ text }))
    : [];

  const payload = {
    date: formData.get("date"),
    title: formData.get("title"),
    context: formData.get("context"),
    constraints,
  };

  try {
    const response = await fetch(`${apiBase}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("Failed to create decision");
    const data = await response.json();
    setOutput({ message: "Decision created", decision: data });
  } catch (error) {
    handleError(error);
  }
});

assumptionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(assumptionForm);
  const decisionId = formData.get("decisionId");
  const assumptions = formData
    .get("assumptions")
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((text) => ({ text }));

  try {
    const response = await fetch(
      `${apiBase}/decision/${decisionId}/assumptions`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(assumptions),
      }
    );
    if (!response.ok) throw new Error("Failed to attach assumptions");
    const data = await response.json();
    setOutput({ message: "Assumptions attached", assumptions: data });
  } catch (error) {
    handleError(error);
  }
});

outcomeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(outcomeForm);
  const decisionId = formData.get("decisionId");
  const payload = { text: formData.get("outcome") };

  try {
    const response = await fetch(`${apiBase}/decision/${decisionId}/outcome`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("Failed to attach outcome");
    const data = await response.json();
    setOutput({ message: "Outcome attached", outcome: data });
  } catch (error) {
    handleError(error);
  }
});

reflectionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(reflectionForm);
  const decisionId = formData.get("decisionId");

  try {
    const response = await fetch(
      `${apiBase}/decision/${decisionId}/reflection`
    );
    if (!response.ok) throw new Error("Failed to fetch reflection");
    const data = await response.json();
    setOutput(data);
  } catch (error) {
    handleError(error);
  }
});
