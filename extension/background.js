// Create a context menu item
chrome.contextMenus.create({
    id: "clustering",
    title: "Clustering",
    contexts: ["all"],
  });

  chrome.contextMenus.create({
    id: "regression",
    title: "Regression",
    contexts: ["all"],
  });

// Event listener for the context menu item
chrome.contextMenus.onClicked.addListener(function (info) {
    if (info.menuItemId === "clustering") {
      // Get the selected text
      console.log("info",info);
      console.log("info",info.linkUrl);

      var selectedText = info.selectionText;
      console.log("selectedText",selectedText); 

      if (info.pageUrl === null || info.pageUrl === undefined ) {
        // pass an alter message 
        showAlert("Error", "The text you selected is not a URL link");         
      }
      else {
        // Pass the URL link to the event handler
        showAlert("Info", "The dataset has been sent and analysis is in progress");
        sendURLLink(info.pageUrl); 
      }
    }
  });
  
  // Event handler for the URL link
  function sendURLLink(url) {
    
    // post the URL link to the server
    
    fetch(`http://0.0.0.0:8000/clustering?txt=${url}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }, 
    })
    .then(response => response.json())
    .then(data => {
      
      console.log('Success:', data); 
      if (data.status === '404') {
      console.log('Success:', data);         
            showAlert("Error", "Error in sending the URL link to the server");
            return {
                "error": data.message,
                "message": "Error in sending the URL link to the server"
            }
        } 
         
        if (data.status === '200') {    
           
          let shareUrl = data.url; 
          let imageUrl = `${shareUrl}&:format=png` 
          // downloadImage(imageUrl);

            setTimeout(function(){
              chrome.notifications.create('notificationId', {
                type: 'basic',
                iconUrl: 'Square.png',
                title: 'Tableau Link',
                message: 'Click here to open sharable dashboard',
              }, function(notificationId) { 
                chrome.notifications.onClicked.addListener(function(clickedNotificationId) {
                  if (clickedNotificationId === notificationId) { 
                    chrome.tabs.create({ url: shareUrl });
                  }
                });
              });
          }, 2000); 

          setTimeout(function(){
              showAlert("Success", "Clustering is complete and the results are available in the dashboard");
          }, 2000);
          return data;
        } 
    })
    .catch((error) => {
        console.error('Error:', error); 
        setTimeout(function(){
            showAlert("Error", error);
        }, 2000);
        return {
            "error": error,
            "message": "Error in sending the URL link to the server"
        }
    });    

    console.log("URL Link:", url); 
  }
  

  // Function to show an alert notification
  function showAlert(title, message) {
    var options = {
      type: "basic",
      iconUrl: "Square.png",
      title: title,
      message: message,
    };
  
    chrome.notifications.create("", options);
  }


// Function to download an image
function downloadImage(url) {
  // Use the chrome.downloads.download() method to initiate the download
  chrome.downloads.download({
    url: url,
    saveAs: true
  }, function (downloadId) {
    // Optional: Handle the download completion or errors
    if (chrome.runtime.lastError) {
      console.error(chrome.runtime.lastError);
      // Handle download error
    } else {
      console.log("Image download started with ID: " + downloadId);
      // Handle download success
    }
  });
}
