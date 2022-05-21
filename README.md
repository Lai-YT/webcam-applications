[![CodeFactor](https://www.codefactor.io/repository/github/lai-yt/webcam-applications/badge)](https://www.codefactor.io/repository/github/lai-yt/webcam-applications)

# A system of student engagement analysis and self-adjusting eye protection

Under the epidemic, online teaching has gradually become a common teaching pattern. How to attract students' attention when teaching online becomes a big challenge. It's difficult for teachers to know the degree of concentration (DoC) of students when teaching since teachers can't directly see the students' face, so it's impossible to adjust the teaching rhythm in real time. \
Therefore, this study combines **face detection**, **deep learning**, **fuzzy control** and many other technologies to design several algorithms for extracting students'
state, and multiple metrics such as **distance**, **posture**, and **blink frequency** are generated. We use these metrics to grade the DoCs of students, and the changes of DoCs are further presented by means of images.
While teaching online, these DoCs are transmitted to the teacher, so that the teacher can instantly know the students' attention with respect to the teaching content.

## Student-end

The **GUI view** of the *Student-end*. \
<img src="./gui/assets/student-view.png" alt="Student view" width=640 height=366>

## Teacher-end

The **monitor view** of the *Teacher-end*. \
<img src="./teacher/assets/monitor-view.png" alt="monitor view" width=640 height=536>

The **history plot** after the grade of a specific student is clicked. \
<img src="./teacher/assets/history-plot.png" alt="history plot" width=640 height=317>
