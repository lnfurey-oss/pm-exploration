const premortemForm = document.getElementById("premortem-form");
const reflectionOutput = document.getElementById("reflection-output");

const setOutput = (payload) => {
  reflectionOutput.textContent = JSON.stringify(payload, null, 2);
};

const handleError = (error) => {
  setOutput({ error: error.message || "Something went wrong" });
};

premortemForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(premortemForm);
  const payload = {
    user_name: formData.get("user_name"),
    user_email: formData.get("user_email"),
    initiative_name: formData.get("initiative_name"),
    concern_text: formData.get("concern_text"),
    observed_signals: formData.get("observed_signals") || null,
    severity: formData.get("severity"),
    impact_level: formData.get("impact_level"),
  };

  try {
    const response = await fetch("/premortem/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Failed to generate action set: ${errText}`);
    }
    const data = await response.json();
    setOutput(data);
  } catch (error) {
    handleError(error);
  }
});
