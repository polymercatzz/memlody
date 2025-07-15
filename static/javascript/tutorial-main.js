const images = [
    "/static/img/tutorial-main1.png",
    "/static/img/tutorial-main2.png",
    "/static/img/tutorial-main3.png",
    "/static/img/tutorial-main4.png",
    "/static/img/tutorial-main5.png",
    "/static/img/tutorial-main6.png",
    "/static/img/tutorial-main7.png",
    "/static/img/tutorial-main8.png",
    "/static/img/tutorial-main9.png"
];
let currentSlide = 0;
let tutorialModal, imageEl, dotsEl;
function renderDots(){
    dotsEl.innerHTML = "";
    for (let i = 0; i < images.length; i++){
        const dot = document.createElement("span");
        dot.className = "w-3 h-3 rounded-full mx-1 cursor-pointer transition-all duration-200 " + (i === currentSlide ? "bg-blue-600 scale-110" : "bg-gray-300");
        dot.addEventListener("click", () => {
        currentSlide = i;
        showSlide(currentSlide);
        });
        dotsEl.appendChild(dot);
    }
}
function showSlide(index){
    if (index >= images.length){
        localStorage.setItem("tutorialSeen", "true");
        closeTutorial();
        return;
    }
    imageEl.src = images[index];
    renderDots();
}
function nextSlide(){
    currentSlide++;
    showSlide(currentSlide);
}
function closeTutorial() {
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
    imageEl = document.getElementById("tutorialImage");
    dotsEl = document.getElementById("dots");
        
    const seen = localStorage.getItem("tutorialSeen");
    if (!seen){
        openTutorial(true);
    }
});