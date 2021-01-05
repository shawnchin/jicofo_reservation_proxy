# Jicofo Reservation Proxy

A small flask app that accepts calls from 
[Jicofo reservation API](https://github.com/jitsi/jicofo/blob/master/doc/reservation.md) and forwards it on to custom
handler. 

### Why this proxy?

So we can:

1. Workaround [unexpected behaviour with Jicofo](https://community.jitsi.org/t/jicofo-reservation-reuse-room-after-expiring/69243/5)
when DELETE endpoint not implemented or temporarily unavailable. Proxy will always return a 200, and backend has 
more flexibility to ignore or deal with errors.
2. Implement custom authentication (TLS client auth, API key, etc) with backend without patching Jicofo.
3. Map API calls to arbitrary backend endpoints i.e. not restricted to `/conference` as expected by Jicofo.
4. Route reservation requests for different room names to different backends.


### Setup

1. Subclass `jicofo_reservation_proxy.service.ServiceBase` to implement your custom backend. 
   * _The default that comes with
this package (`DummyService`) is a placeholder implementation that accepts all conference creation requests and keeps 
track of meetings in memory. Useful to test interconnectivity with Jicofo, but not much else._

2. [Deploy](https://flask.palletsprojects.com/en/1.1.x/deploying/) the flask app. 
   * Pass in your custom service class when creating the flask app. E.g.
       ```python
       from jicofo_reservation_proxy import create_app
       from your_package import CustomServiceClass

       app = create_app(service_class=CustomServiceClass)
       ```
   * You'll probably want the service accessible only by Jicofo e.g. run on same host as Jicofo and listening only 
   to `127.0.0.1:7777`
   
3. Configure Jicofo and set the REST API endpoint to the flask app, e.g.
    ```java
    org.jitsi.impl.reservation.rest.BASE_URL=http://127.0.0.1:7777
    ```
    