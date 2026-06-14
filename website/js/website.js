async function loadPublicStats() {
    const earlyAccessCount = document.getElementById("earlyAccessCount");
    const betaApplicationCount = document.getElementById("betaApplicationCount");
    const totalWaitlistCount = document.getElementById("totalWaitlistCount");

    if (!earlyAccessCount || !betaApplicationCount || !totalWaitlistCount) {
        return;
    }

    try {
        const response = await fetch("http://localhost:8090/public/stats");
        const stats = await response.json();

        earlyAccessCount.textContent = stats.early_access_count;
        betaApplicationCount.textContent = stats.beta_application_count;
        totalWaitlistCount.textContent = stats.total_waitlist_count;

    } catch (error) {
        earlyAccessCount.textContent = "—";
        betaApplicationCount.textContent = "—";
        totalWaitlistCount.textContent = "—";
    }
}

function startLaunchCountdown() {
    const daysElement = document.getElementById("countdownDays");
    const hoursElement = document.getElementById("countdownHours");
    const minutesElement = document.getElementById("countdownMinutes");
    const secondsElement = document.getElementById("countdownSeconds");

    if (!daysElement || !hoursElement || !minutesElement || !secondsElement) {
        return;
    }

    const launchDate = new Date("2026-09-07T09:00:00").getTime();

    function updateCountdown() {
        const now = new Date().getTime();
        const distance = launchDate - now;

        if (distance <= 0) {
            daysElement.textContent = "0";
            hoursElement.textContent = "0";
            minutesElement.textContent = "0";
            secondsElement.textContent = "0";
            return;
        }

        daysElement.textContent = Math.floor(distance / (1000 * 60 * 60 * 24));
        hoursElement.textContent = Math.floor((distance / (1000 * 60 * 60)) % 24);
        minutesElement.textContent = Math.floor((distance / (1000 * 60)) % 60);
        secondsElement.textContent = Math.floor((distance / 1000) % 60);
    }

    updateCountdown();
    setInterval(updateCountdown, 1000);
}

async function loadFeatureVotes() {
    const featureVoteList = document.getElementById("featureVoteList");

    if (!featureVoteList) {
        return;
    }

    try {
        const response = await fetch("http://localhost:8090/public/feature-votes");
        const features = await response.json();

        featureVoteList.innerHTML = features.map(item => `
            <div class="feature-vote-card">
                <div>
                    <strong>${item.feature}</strong>
                    <span>${item.votes} votes</span>
                </div>

                <button onclick="submitFeatureVote('${item.feature}')">
                    Vote
                </button>
            </div>
        `).join("");

    } catch (error) {
        featureVoteList.innerHTML = "<p>Feature voting is temporarily unavailable.</p>";
    }
}


async function submitFeatureVote(feature) {
    try {
        const response = await fetch(
            `http://localhost:8090/public/feature-votes/${encodeURIComponent(feature)}`,
            {
                method: "POST"
            }
        );

        const result = await response.json();

        alert(result.message || result.detail);

        loadFeatureVotes();

    } catch (error) {
        alert("Unable to submit vote.");
    }
}

document.addEventListener("DOMContentLoaded", function () {
    loadFeatureVotes();
    startLaunchCountdown();
    loadPublicStats();
    const mobileMenuButton = document.getElementById("mobileMenuButton");
    const navLinks = document.querySelector(".nav-links");

    if (mobileMenuButton && navLinks) {
        mobileMenuButton.addEventListener("click", function () {
            navLinks.classList.toggle("open");
        });

        navLinks.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                navLinks.classList.remove("open");
            });
        });
    }

    document.querySelectorAll(".coming-soon").forEach(function (button) {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            alert("Nexora download links are coming soon.");
        });
    });

    const earlyAccessForm = document.getElementById("earlyAccessForm");
    const earlyAccessMessage = document.getElementById("earlyAccessMessage");

    if (earlyAccessForm && earlyAccessMessage) {
        earlyAccessForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const name = document.getElementById("earlyName").value.trim();
            const email = document.getElementById("earlyEmail").value.trim();
            const experience = document.getElementById("earlyExperience").value;

            if (!name || !email || !experience) {
                earlyAccessMessage.textContent = "Please complete all fields.";
                return;
            }

            try {
                const response = await fetch("http://localhost:8090/early-access", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        name: name,
                        email: email,
                        experience: experience,
                    }),
                });

                const result = await response.json();

                earlyAccessMessage.textContent = result.message;
                earlyAccessForm.reset();

            } catch (error) {
                earlyAccessMessage.textContent = "Unable to join early access right now.";
            }
        });
    }

const betaApplicationForm = document.getElementById("betaApplicationForm");
const betaApplicationMessage = document.getElementById("betaApplicationMessage");

if (betaApplicationForm && betaApplicationMessage) {

    betaApplicationForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const payload = {
            name: document.getElementById("betaName").value.trim(),
            email: document.getElementById("betaEmail").value.trim(),
            experience: document.getElementById("betaExperience").value,
            trading_goal: document.getElementById("betaTradingGoal").value.trim(),
            beta_reason: document.getElementById("betaReason").value.trim()
        };

        try {

            const response = await fetch(
                "http://localhost:8090/beta-application",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                }
            );

            const result = await response.json();

            betaApplicationMessage.textContent = result.message;

            if (result.status === "success") {
                betaApplicationForm.reset();
            }

        } catch (error) {

            betaApplicationMessage.textContent =
                "Unable to submit beta application right now.";

        }

    });

}

    const lightbox = document.getElementById("screenshotLightbox");
    const lightboxImage = document.getElementById("lightboxImage");
    const closeLightbox = document.getElementById("closeLightbox");

    if (lightbox && lightboxImage) {
        document.querySelectorAll(".preview-lightbox-img").forEach(function (image) {
            image.addEventListener("click", function () {
                lightboxImage.src = image.src;
                lightboxImage.alt = image.alt;
                lightbox.classList.add("active");
            });
        });

        if (closeLightbox) {
            closeLightbox.addEventListener("click", function () {
                lightbox.classList.remove("active");
                lightboxImage.src = "";
            });
        }

        lightbox.addEventListener("click", function (event) {
            if (event.target === lightbox) {
                lightbox.classList.remove("active");
                lightboxImage.src = "";
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                lightbox.classList.remove("active");
                lightboxImage.src = "";
            }
        });
    }

    document.querySelectorAll(".faq-question").forEach(function (button) {
        button.addEventListener("click", function () {
            const item = button.parentElement;
            item.classList.toggle("active");
        });
    });
});
