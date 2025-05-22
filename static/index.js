
let hcaptchaReady = false;
let currentTaskId = null;
let taskInProgress = false;

const socket = io();

function onHcaptchaLoad() {
    console.log("✅ hCaptcha API loaded");
    hcaptchaReady = true;

    // Request initial task once hCaptcha is ready
    socket.emit("request_task");
}

// Listen for task assignment from backend
socket.on("assign_task", (data) => {
    console.log("📩 Task assigned from backend:", data);

    if (data.task_id && hcaptchaReady && !taskInProgress) {
        currentTaskId = data.task_id;
        taskInProgress = true;
        hcaptcha.execute();  // Trigger hCaptcha
    } else if (!data.task_id) {
        console.log("⏳ No task in queue. Waiting...");
        setTimeout(() => {
            socket.emit("request_task");  // Retry later
        }, 5000);
    }
});

// After successful challenge
function onVerify(token) {
    console.log("✅ hCaptcha verified for task:", currentTaskId);

    // Show the loading overlay
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'flex';

    if (!currentTaskId) {
        console.error("❌ No task ID to associate with token.");
        return;
    }

    // Submit token with task ID
    socket.emit("submit_token", {
        token: token,
        task_id: currentTaskId,
    });

    // Reset task state
    taskInProgress = false;
    currentTaskId = null;

    // Reload hCaptcha and request next task after short delay
    setTimeout(() => {
        hcaptcha.reset();
        socket.emit("request_task");

        // ✅ Reload page after requesting next task
        //window.location.reload();
    }, 4500);
}
