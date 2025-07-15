let currentSlide = 0;
let tutorialModal, dotsEl, imageEls;

function renderDots(){
    dotsEl.innerHTML = "";
    for (let i = 0; i < imageEls.length; i++) {
        const dot = document.createElement("span");
        dot.className = "w-3 h-3 rounded-full mx-1 cursor-pointer transition-all duration-200 " + 
                        (i === currentSlide ? "bg-blue-600 scale-110" : "bg-gray-300");
        dot.addEventListener("click", () => {
            currentSlide = i;
            showSlide(currentSlide);
        });
        dotsEl.appendChild(dot);
    }
}
function showSlide(index){
    if (index >= imageEls.length) {
        localStorage.setItem("tutorialSeen", "true");
        closeTutorial();
        return;
    }
    imageEls.forEach((img, i) => {
        img.classList.toggle("active", i === index);
    });

    renderDots();
}
function nextSlide(){
    currentSlide++;
    showSlide(currentSlide);
}
function closeTutorial(){
    tutorialModal.style.display = "none";
}
function openTutorial(force = false){
    const seen = localStorage.getItem("tutorialSeen");
    if (seen === "true" && !force) return;
    currentSlide = 0;
    showSlide(currentSlide);
    tutorialModal.style.display = "flex";
}
window.addEventListener("DOMContentLoaded", () => {
    tutorialModal = document.getElementById("tutorialModal");
    dotsEl = document.getElementById("dots");
    imageEls = Array.from(document.querySelectorAll(".tutorial-slide"));
    const seen = localStorage.getItem("tutorialSeen");
    if (!seen) {
        openTutorial(true);
    }
});