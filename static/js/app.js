function previewTheme(theme) {
    document.getElementById("theme-stylesheet").href = `/static/css/${theme}.css`;
}

document.addEventListener("DOMContentLoaded", () => {
    // Portfolio creation
    const portfolioForm = document.getElementById("portfolio-form");
    if (portfolioForm) {
        portfolioForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(portfolioForm);
            const response = await fetch("/portfolios", {
                method: "POST",
                body: formData
            });
            const result = await response.json();
            alert(result.message || result.error);
            if (response.ok) {
                portfolioForm.reset();
            }
        });
    }

    // Case study creation
    const caseStudyForm = document.getElementById("case-study-form");
    if (caseStudyForm) {
        caseStudyForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(caseStudyForm);
            const response = await fetch("/case_studies", {
                method: "POST",
                body: formData
            });
            const result = await response.json();
            alert(result.message || result.error);
            if (response.ok) {
                caseStudyForm.reset();
            }
        });
    }

    // Analytics tracking
    const caseStudies = document.querySelectorAll(".case-study");
    caseStudies.forEach(cs => {
        cs.addEventListener("click", () => {
            const caseStudyId = cs.dataset.id;
            fetch(`/analytics/${caseStudyId}/track?action=click`, {
                method: "POST"
            });
        });
    });
});