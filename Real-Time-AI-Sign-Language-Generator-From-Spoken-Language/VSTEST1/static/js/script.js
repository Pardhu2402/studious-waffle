// Add this function to display sentiment
function displaySentiment(sentiment) {
    const sentimentDiv = document.createElement('div');
    sentimentDiv.className = `sentiment-indicator sentiment-${sentiment}`;
    sentimentDiv.textContent = `Mood: ${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}`;
    
    // Find the output container
    const outputContainer = document.querySelector('.output-container');
    // Add the sentiment indicator after the text display
    outputContainer.appendChild(sentimentDiv);
}

// Update your existing audio processing function
function processAudio(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);

    fetch('/process_audio', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }
        
        // Display the transcribed text
        const textDisplay = document.createElement('p');
        textDisplay.textContent = `Text: ${data.text}`;
        document.querySelector('.output-container').appendChild(textDisplay);
        
        // Display sentiment
        displaySentiment(data.sentiment);
        
        // Display sign language videos/images
        if (data.sign_paths && data.sign_paths.length > 0) {
            displaySignLanguage(data.sign_paths);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Update the form submission handler
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('Form submission started');

    const formData = new FormData();
    const wordInput = document.getElementById('wordInput').value;
    const languageSelect = document.getElementById('languageSelect').value;
    const fileType = document.getElementById('fileType').value;
    const fileInput = document.getElementById('fileInput').files[0];
    const description = document.getElementById('description').value;

    // Log the data being sent
    console.log('Uploading:', {
        word: wordInput,
        language: languageSelect,
        type: fileType,
        file: fileInput,
        description: description
    });

    formData.append('word', wordInput);
    formData.append('language', languageSelect);
    formData.append('type', fileType);
    formData.append('file', fileInput);
    formData.append('description', description);

    try {
        const response = await fetch('/upload_sign', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        console.log('Server response:', data);

        if (data.success) {
            alert('File uploaded successfully!');
            this.reset();
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Error uploading file: ' + error.message);
    }
});

// Update the file input validation
document.getElementById('fileInput').addEventListener('change', function(e) {
    const file = this.files[0];
    const fileType = document.getElementById('fileType').value;
    
    if (file) {
        console.log('File selected:', file.name, 'Size:', file.size, 'Type:', file.type);
        
        if (fileType === 'video' && !file.type.startsWith('video/')) {
            alert('Please select a video file when video type is selected');
            this.value = '';
            return;
        }
        
        if (fileType === 'image' && !file.type.startsWith('image/')) {
            alert('Please select an image file when image type is selected');
            this.value = '';
            return;
        }
    }
});

// Update file type validation when changed
document.getElementById('fileType').addEventListener('change', function() {
    const fileInput = document.getElementById('fileInput');
    if (this.value === 'video') {
        fileInput.accept = 'video/mp4';
    } else {
        fileInput.accept = 'image/jpeg,image/jpg,image/png';
    }
    fileInput.value = ''; // Clear the current selection
}); 