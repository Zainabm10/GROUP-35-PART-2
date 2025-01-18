// פונקציה שמטפלת בלחיצה על כפתור
document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("button");
    if (button) {
        button.addEventListener("click", () => {
            alert("Button clicked!");
        });
    }
});

// פונקציה שמטפלת בשינוי ערך בתיבת טקסט
const handleInputChange = () => {
    const input = document.querySelector("#email");
    if (input) {
        input.addEventListener("input", (event) => {
            console.log("Input value changed to:", event.target.value);
        });
    }
};

// הפעלת הפונקציה
handleInputChange();
