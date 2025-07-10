const score = 100;
const crown = document.getElementById("crown");
if (score <= 0){
    crown.style.clipPath = 'inset(100% 0 0 0)';
    crown.style.fill = 'none';
}else if (score >= 100){
    crown.style.clipPath = 'inset(0 0 0 0)';
    crown.style.fill = 'url(#goldGradient)';
}else{
    const insetBottom = 100 - score;
    crown.style.clipPath = `inset(${insetBottom}% 0 0 0)`;
    crown.style.fill = 'url(#goldGradient)';
}