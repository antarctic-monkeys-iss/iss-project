// script.js
const dropzone = document.getElementById('dropzone');
const uploadedImages = document.getElementById('uploaded-images');


dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
  dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  const files = e.dataTransfer.files;
  handleFiles(files);
});

dropzone.addEventListener('click', () => {
  const fileInput = dropzone.querySelector('input[type="file"]');
  fileInput.click();
});

dropzone.querySelector('input[type="file"]').addEventListener('change', (e) => {
  const files = e.target.files;
  handleFiles(files);
});

function handleFiles(files) {
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const reader = new FileReader();

    reader.onload = (e) => {
      const imageContainer = document.createElement('div');
      imageContainer.classList.add('uploaded-image-container');

      const image = document.createElement('img');
      image.src = e.target.result;
      image.classList.add('uploaded-image');

      imageContainer.appendChild(image);
      uploadedImages.appendChild(imageContainer);

      image.alt = file.name;

      imageContainer.addEventListener('click', () => {
        imageContainer.classList.toggle('selected');
      });
    };

    reader.readAsDataURL(file);
  }
}

function uploadImages() {
  const imageContainers = document.querySelectorAll('.uploaded-image-container.selected');
  const formData = new FormData();
  const images = new Set();
  const names = new Set();

  imageContainers.forEach(container => {
    const img = container.querySelector('img');
    const file = dataURLtoFile(img.src, images);
    formData.append('images', file);
    formData.append('names', img.alt); 
    names.add(img.alt);
  });

  addToGallery(images, names);


  fetch('/upload-images', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    console.log(data);
    // Handle the response as needed
  })
  .catch(error => console.error('Error:', error));

  removeImages();
}

function dataURLtoFile(dataurl, images) {
  const arr = dataurl.split(',');
  const mime = arr[0].match(/:(.*?);/)[1];
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  const x = new Blob([u8arr], { type: mime })
  images.add(x)
  return x;
}

function removeImages() {
  const selectedImageContainers = document.querySelectorAll('.uploaded-image-container.selected');

  selectedImageContainers.forEach(container => {
    container.remove(); // Remove the selected image container
  });
}

function selectAll() {
  const imageContainers = document.querySelectorAll('.uploaded-image-container');
  imageContainers.forEach((container) => {
    container.classList.add('selected');
  });
}

function unselectAll() {
  const imageContainers = document.querySelectorAll('.uploaded-image-container');
  imageContainers.forEach((container) => {
    container.classList.remove('selected');
  });
}

function previewVideo() {
  var selectedPhotos = [];
  var selectedImages = document.querySelectorAll('.uploaded-image-container.selected img');
  selectedImages.forEach((image) => {
    selectedPhotos.push(image.src);
  });

  var videoUrl = '/preview-video?photos=' + selectedPhotos + '&music=' + backgroundMusic + '&duration=' + imageDuration + '&transition=' + selectedTransition;

  document.getElementById('videoPreview').src = videoUrl;
}

function generateVideo() {
  var resolution = document.getElementById('resolution').value;
  var quality = document.getElementById('quality').value;
  // Implement AJAX request or form submission to send data to the backend
}
function redirectToLogin() {
  window.location.href = 'login.html';
}

function validateSignupForm() {
  var name = document.getElementById('signupName').value;
  var email = document.getElementById('signupEmail').value;
  var password = document.getElementById('signupPassword').value;
  // Add validation logic here
  return true; // Return true to allow form submission, false to prevent submission
}

function validateLoginForm() {
  var email = document.getElementById('loginEmail').value;
  var password = document.getElementById('loginPassword').value;
  // Add validation logic here
  return true; // Return true to allow form submission, false to prevent submission
}


const dropzoneMusic = document.getElementById('musicDropbox');
const uploadedMusic = document.getElementById('uploadedMusic');

dropzoneMusic.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzoneMusic.classList.add('dragover');
});

dropzoneMusic.addEventListener('dragleave', () => {
  dropzoneMusic.classList.remove('dragover');
});

dropzoneMusic.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzoneMusic.classList.remove('dragover');
  const files = e.dataTransfer.files;
  handleMusicFiles(files);
});

dropzoneMusic.addEventListener('click', () => {
  const fileInput = dropzoneMusic.querySelector('input[type="file"]');
  fileInput.click();
});

dropzoneMusic.querySelector('input[type="file"]').addEventListener('change', (e) => {
  const files = e.target.files;
  handleMusicFiles(files);
});

function handleMusicFiles(files) {
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const musicContainer = document.createElement('tr');
    musicContainer.classList.add('uploaded-music-row');

    const musicFileName = document.createElement('td');
    musicFileName.textContent = file.name;

    const selectButton = document.createElement('button');
    selectButton.textContent = 'Select';
    selectButton.style.margin = '5px';
    selectButton.addEventListener('click', () => selectMusic(file, musicFileName.textContent));

    const buttonContainer = document.createElement('td');
    buttonContainer.appendChild(selectButton);

    musicContainer.appendChild(musicFileName);
    musicContainer.appendChild(buttonContainer);
    uploadedMusic.querySelector('tbody').appendChild(musicContainer);

    function selectMusic(file, songName) {
      const formData = new FormData();
      const songContentBlob = new Blob([file], { type: file.type });
      formData.append('song_name', songName);
      formData.append('song_content', songContentBlob);
      uploadSong(formData, songName);
      
      var newRow = document.createElement('tr');
      var songNameCell = document.createElement('td');
      songNameCell.textContent = musicFileName.textContent;
      newRow.appendChild(songNameCell);
      
      var buttonCell = document.createElement('td');
      var removeButton = document.createElement('button');
      removeButton.textContent = 'Remove';
      removeButton.classList.add('select-button');
      removeButton.setAttribute('data-song-name', songName);
      removeButton.onclick = function() {
        get_rid_off(this);
        row.remove(); 
      };
      buttonCell.appendChild(removeButton);
      newRow.appendChild(buttonCell);
      document.querySelector('#selectedMusic tbody').appendChild(newRow);
    
      console.log(`Selected: ${songName}`);
    }

    function uploadSong(formData, songName) {
      fetch('/upload-song', {
        method: 'POST',
        body: formData,
        headers: {
          // If needed, add headers like authorization token or content type
        },
      })
        .then(response => response.json())
        .then(data => {
          console.log(data);
          // Handle the response as needed
          // For example, update UI or show a success message
        })
        .catch(error => {
          console.error('Error:', error);
          // Handle errors, show error messages, etc.
        });
    }

    function removeSong(formData, songName) {
      fetch('/remove-song', {
        method: 'POST',
        body: formData,
        headers: {
          // If needed, add headers like authorization token or content type
        },
      })
        .then(response => response.json())
        .then(data => {
          console.log(data);
          // Handle the response as needed
          // For example, update UI or show a success message
        })
        .catch(error => {
          console.error('Error:', error);
          // Handle errors, show error messages, etc.
        });
    }

    // Use Web Audio API to get audio duration
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const reader = new FileReader();

    reader.readAsArrayBuffer(file);
  }
}

// New: Play and Stop functions
let audioBufferSource = null;

function playMusic(file) {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const reader = new FileReader();

  reader.onload = function (e) {
    audioContext.decodeAudioData(e.target.result, function (buffer) {
      if (audioBufferSource) {
        audioBufferSource.stop();
      }

      audioBufferSource = audioContext.createBufferSource();
      audioBufferSource.buffer = buffer;
      audioBufferSource.connect(audioContext.destination);
      audioBufferSource.start();
    });
  };

  reader.readAsArrayBuffer(file);
}

function stopMusic() {
  if (audioBufferSource) {
    audioBufferSource.stop();
  }
}

function formatDuration(durationInSeconds) {
  const minutes = Math.floor(durationInSeconds / 60);
  const seconds = Math.round(durationInSeconds % 60);
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

const galleryItems = document.querySelectorAll('.gallery-item');
galleryItems.forEach(item => {
  item.addEventListener('click', () => {
    item.classList.toggle('selected');
  });
});

function addToGallery(images, names) {
  const galleryContainer = document.querySelector('.gallery-container');

  const errorParagraph = document.querySelector('.gallery-container p');
  if (errorParagraph) {
    errorParagraph.style.display = 'none';
  }

  images.forEach((imageBlob, index) => {
    const imageItem = document.createElement('div');
    imageItem.classList.add('gallery-item');

    const image = document.createElement('img');

    const reader = new FileReader();
    reader.onload = function () {
      image.src = reader.result;
    };
    reader.readAsDataURL(imageBlob);

    // Set the alt attribute to the corresponding name from the names array
    image.alt = names[index];

    image.classList.add("gallery-img");
    imageItem.appendChild(image);
    galleryContainer.appendChild(imageItem);

    image.addEventListener('click', function() {
      imageItem.classList.toggle('selected');
    });

  });
}

function getBlobForGallery(dataurl) {
  const arr = dataurl.split(',');
  const mime = arr[0].match(/:(.*?);/)[1];
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  const x = new Blob([u8arr], { type: mime })
  return x;
}

function RemoveImagesFromGallery() {
  const selectedImageContainers = document.querySelectorAll('.gallery-item.selected');
  const formData = new FormData();
  const images = new Set();
  selectedImageContainers.forEach(container => {
    const img = container.querySelector('img');
    const file = getBlobForGallery(img.src, images);
    formData.append('images', file);
  });

  fetch('/remove-item-from-gallery', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    console.log(data);
  })
  .catch(error => console.error('Error:', error));

  selectedImageContainers.forEach(container => {
    container.remove(); // Remove the selected image container
  });

}
