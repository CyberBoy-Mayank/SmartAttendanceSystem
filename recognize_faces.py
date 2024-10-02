import cv2
import os
import csv
import datetime
import mediapipe as mp
from tkinter import messagebox  # Import messagebox for confirmation

class FaceRecognizer:
    def __init__(self, camera_index=0):  # External webcam
        self.cap = cv2.VideoCapture(camera_index)
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.recognizer.read('trainer.yml')

        # Haar Cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        self.names = self.load_names()
        self.attendance_dir = "attendance"
        os.makedirs(self.attendance_dir, exist_ok=True)
        self.attendance_file = os.path.join(self.attendance_dir, f"{datetime.datetime.now().strftime('%Y-%m-%d')}.csv")

        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(max_num_faces=1)

        # Store previous eyebrow positions to detect movement
        self.previous_eyebrow_distance = None

        # Track attendance status (to keep color green after marking attendance)
        self.attendance_status = {}

    def load_names(self):
        """Load user names and IDs from the names.csv file."""
        names = {}
        try:
            with open('names.csv', 'r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip the header row
                for row in reader:
                    names[int(row[0])] = row[1]
        except Exception as e:
            messagebox.showerror("Error", f"Error loading names: {e}")
        return names

    def attendance_already_marked(self, name):
        """Check if attendance has already been marked for the user today."""
        try:
            if os.path.isfile(self.attendance_file):
                with open(self.attendance_file, mode='r') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if row[1] == name:  # Check by Name
                            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error checking attendance: {e}")
        return False

    def mark_attendance(self, id_, name):
        """Mark attendance for the user if not already marked today."""
        try:
            if not self.attendance_already_marked(name):
                with open(self.attendance_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([id_, name, datetime.datetime.now().strftime('%H:%M:%S')])
                    messagebox.showinfo(f"Attendance marked for {name} (ID: {id_}).")
                    self.attendance_status[name] = True  # Set status to True after marking
            else:
                messagebox.showinfo(f"Attendance already marked for {name} today.")
        except Exception as e:
            messagebox.showerror("Error", f"Error marking attendance: {e}")

    def calculate_eyebrow_movement(self, face_landmarks, face_box):
        """Calculate the distance between eyebrows and eyes to detect eyebrow movement."""
        x, y, w, h = face_box  # Face bounding box coordinates

        # Get landmark points for the left eyebrow and left eye
        left_eyebrow_y = face_landmarks.landmark[105].y * h + y  # Left eyebrow (landmark 105)
        left_eye_y = face_landmarks.landmark[33].y * h + y       # Left eye (landmark 33)

        # Calculate the vertical distance between the eyebrow and the eye
        eyebrow_to_eye_distance = abs(left_eyebrow_y - left_eye_y)

        if self.previous_eyebrow_distance is not None:
            # Check if the eyebrow moved up and down significantly
            if abs(self.previous_eyebrow_distance - eyebrow_to_eye_distance) > 5:  # You can adjust this threshold
                return True

        # Update the previous distance for the next frame
        self.previous_eyebrow_distance = eyebrow_to_eye_distance
        return False

    def draw_landmark_points(self, frame, face_landmarks, face_box, color):
        """Draw all 468 facial landmark points only within the detected face."""
        x, y, w, h = face_box  # Get the face bounding box coordinates
        for landmark in face_landmarks.landmark:
            # Convert normalized landmark coordinates to the bounding box's pixel values
            landmark_x = int(landmark.x * w) + x
            landmark_y = int(landmark.y * h) + y

            # Draw a small circle for each landmark point only on the face
            cv2.circle(frame, (landmark_x, landmark_y), 1, color, -1)

    def recognize_faces(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                messagebox.showerror("Error", "Failed to grab frame. Exiting...")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # For face mesh processing
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                face = gray[y:y + h, x:x + w]
                id_, conf = self.recognizer.predict(face)
                name = self.names.get(id_, "Unknown")
                color = (255, 0, 0)  # Default to blue (BGR) for not marked attendance

                if conf < 50:  # Adjust threshold based on your dataset
                    cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

                    # Detect face mesh landmarks
                    face_rgb = rgb_frame[y:y + h, x:x + w]
                    results = self.face_mesh.process(face_rgb)

                    if results.multi_face_landmarks:
                        for face_landmarks in results.multi_face_landmarks:
                            # Check if the attendance has already been marked for this person
                            if name in self.attendance_status and self.attendance_status[name]:
                                color = (0, 255, 0)  # Green after attendance is marked
                            else:
                                # Check if the eyebrows moved up and down
                                if self.calculate_eyebrow_movement(face_landmarks, (x, y, w, h)):
                                    # Mark attendance if the eyebrow movement is detected
                                    if not self.attendance_already_marked(name):
                                        self.mark_attendance(id_, name)
                                        color = (0, 255, 0)  # Change to green

                            self.draw_landmark_points(frame, face_landmarks, (x, y, w, h), color)

            cv2.imshow("Recognize Faces with Eyebrow Movement", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        recognizer = FaceRecognizer()
        recognizer.recognize_faces()
    except Exception as e:
        print(f"Failed to start face recognition: {e}")
