// content.js

window.addEventListener('message', function (text) {
    chrome.runtime.sendMessage({"message": "change_proxy", "data": `${text.data.params}`});
});

