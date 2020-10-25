// background.js

// This block is new!
chrome.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        if( request.message === "change_proxy" && request.data != "undefined") {
            var curr_proxy = request.data.split(':');
            console.log(curr_proxy[0]);
            chrome.tabs.executeScript({
                code: `var div=document.createElement("p"); document.body.appendChild(div); div.innerText="${curr_proxy[0]}"; div.style.cssText="top:0; margin-left:20px;"`
            });
            var config = {
                mode: "fixed_servers",
                rules: {
                    singleProxy: {
                        scheme: "http",
                        host: curr_proxy[0],
                        port: parseInt(curr_proxy[1])
                    },
                    bypassList: ["localhost"]
                }
            };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: curr_proxy[2],
                        password: curr_proxy[3]
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
            );
        }
        sendResponse();
    }
);