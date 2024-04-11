function openNav() {
  document.getElementById("sidebar").style.width = "250px";
  document.querySelector('.content').style.marginLeft = "250px";
}

function closeNav() {
  document.getElementById("sidebar").style.width = "0";
  document.querySelector('.content').style.marginLeft= "0";
}

function toggleContent1() {
    var contentDiv = document.getElementById("content1");
    var button = document.querySelector(".toggle-button");

    if (contentDiv.style.maxHeight) {
        contentDiv.style.maxHeight = null;
        button.classList.remove("open");
        button.innerHTML = "▼";
    } else {
        contentDiv.style.maxHeight = contentDiv.scrollHeight + "px";
        button.classList.add("open");
        button.innerHTML = "▲";
    }
}

// function toggleContent3() {
//     var contentDiv = document.getElementById("content3");
//     var button = document.querySelector(".toggle-button");

//     if (contentDiv.style.maxHeight) {
//         contentDiv.style.maxHeight = null;
//         button.classList.remove("open");
//         button.innerHTML = "▼";
//     } else {
//         contentDiv.style.maxHeight = contentDiv.scrollHeight + "px";
//         button.classList.add("open");
//         button.innerHTML = "▲";
//     }
// }

// function toggleContent4() {
//     var contentDiv = document.getElementById("content4");
//     var button = document.querySelector(".toggle-button");

//     if (contentDiv.style.maxHeight) {
//         contentDiv.style.maxHeight = null;
//         button.classList.remove("open");
//         button.innerHTML = "▼";
//     } else {
//         contentDiv.style.maxHeight = contentDiv.scrollHeight + "px";
//         button.classList.add("open");
//         button.innerHTML = "▲";
//     }
// }

document.addEventListener('DOMContentLoaded', function() {
    var content2 = document.getElementById('content2');
    var toggleButton2 = document.querySelector('.toggle-button2');

    // Check if content2 is initially visible
    var isContentVisible = content2.classList.contains('show');

    // Toggle content visibility based on initial state
    toggleButton2.textContent = isContentVisible ? '▲' : '▼'; // Change the toggle button text based on initial state

    // Function to toggle content visibility
    function toggleContent2() {
        content2.classList.toggle('show');
        toggleButton2.textContent = content2.classList.contains('show') ? '▲' : '▼'; // Change the toggle button text based on current state
    }

    // Attach toggleContent2 to the window object to make it globally accessible
    window.toggleContent2 = toggleContent2;

    // Function to handle form submission asynchronously
    window.handleFormSubmission = function(form) {
        // Example: Perform AJAX form submission
        var formData = new FormData(form);
        fetch(form.action, {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(data => {
            // Update content or handle response as needed
            console.log('Form submitted successfully:', data);

            // Ensure the content remains open after form submission
            toggleContent2();
        })
        .catch(error => {
            console.error('Error submitting form:', error);
        });
    };
});
