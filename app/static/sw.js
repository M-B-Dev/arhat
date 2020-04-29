// sw.js

'use strict';

/* eslint-disable max-len */

// const applicationServerPublicKey = "BNbxGYNMhEIi9zrneh7mqV4oUanjLUK3m+mYZBc62frMKrEoMk88r3Lk596T0ck9xlT+aok0fO1KXBLV4+XqxYM=";

/* eslint-enable max-len */

function urlB64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

self.addEventListener('push', function(event) {
  console.log('[Service Worker] Push Received.');
  console.log(`[Service Worker] Push had this data: "${event.data.text()}"`);

  const title = 'Task due';
  const options = {
    requireInteraction: true,
    "body": `${event.data.text()}`,
    "icon": "images/ccard.png",
    "actions": [
      { "action": "yes", "title": "Yes", "icon": "images/yes.png" },
      { "action": "no", "title": "No", "icon": "images/no.png" }
    ]
  };

  event.waitUntil(self.registration.showNotification(title, options));
  
});

self.addEventListener('notificationclick', function(event) {
  const channel = new BroadcastChannel('sw-messages');
  console.log('[Service Worker] Notification click Received.');
  switch (event.action) {
    case 'yes':
      console.log('yes');
      channel.postMessage({title: 'Hello from SW'});
      break;
    case 'no':
      console.log('no')
      break;
  }
  event.notification.close();
})

self.addEventListener('pushsubscriptionchange', function(event) {
  console.log('[Service Worker]: \'pushsubscriptionchange\' event fired.');
  const applicationServerPublicKey = localStorage.getItem('applicationServerPublicKey');
  const applicationServerKey = urlB64ToUint8Array(applicationServerPublicKey);
  event.waitUntil(
    self.registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey
    })
    .then(function(newSubscription) {
      // TODO: Send to application server
      console.log('[Service Worker] New subscription: ', newSubscription);
    })
  );
})