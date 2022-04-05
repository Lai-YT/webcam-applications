# Server

The Flask server, works as the relay station between *Student-end* (GUI) and *Teacher-end* (Monitor & Database).

## Constraints

*Server* should be opened without knowing the *Student* and *Teacher*. \
Both of them should perform their own `POST` and `GET` requests to *send* and *receive* data from *Server*.
