// frontend/public/sw.js
console.log("Service Worker Loaded.");

self.addEventListener("push", (event) => {
  console.log("[Service Worker] Push Received.");
  const data = event.data ? event.data.json() : {};

  const title = data.title || "PriceTrackr";
  const options = {
    body: data.body || "Something changed!",
    icon: "/icon-192.png", // You'll need to add an icon here
    badge: "/icon-72.png", // And here
    data: {
      url: data.url || "/",
    },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  console.log("[Service Worker] Notification click Received.");
  event.notification.close();

  const urlToOpen = event.notification.data.url;
  
  event.waitUntil(
    clients.matchAll({ type: "window" }).then((clientsArr) => {
      // If a window is already open, focus it
      const hadWindowToFocus = clientsArr.some((windowClient) =>
        windowClient.url.endsWith(urlToOpen)
          ? (windowClient.focus(), true)
          : false
      );

      // Otherwise, open a new window
      if (!hadWindowToFocus)
        clients.openWindow(urlToOpen).then((windowClient) => windowClient.focus());
    })
  );
});