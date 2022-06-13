# Server

The Flask server, works as the relay station between *Student-end* (GUI & Applications) and *Teacher-end* (Monitor & Database).

## Constraints

*Server* should be opened without knowing the *Student* and *Teacher*. \
Both of them should perform their own `POST` and `GET` requests to *send* and *receive* data from *Server*.

## Web API

### How can I send new data to Server?

- `POST ${server url}/student/grades`: send the new *grade* to Server; the grade sent is reponsed back
- `POST ${server url}/student/screenshots`: send the new *screenshot* to Server; the screenshot sent is reponsed back

### How can I receive data from Server?

- `GET ${server url}`: responses HTML homepage with descriptions but no data
- `GET ${server url}/teacher`: responses the data (grades, screenshots) stored on Server in form of HTML tables; which is the human-readable way to view the data
- `GET ${server url}/teacher?genre=grades`: responses the *grades* stored on Server in JSON, and then Server no longer keeps those grades
```
[
    {
      "start": ...,
      "end": ...,
      ...
    },
    {
      "start": ...,
      "end": ...,
      ...
    },
    ...
]
```
- `GET ${server url}/teacher?genre=screenshots`: responses the *screenshots* stored on Server in JSON, and then Server no longer keeps those screenshots
```
[
    {
      "id": ...,
      "slices": ...,
      ...
    },
    {
      "id": ...,
      "slices": ...,
      ...
    },
    ...
]
```
