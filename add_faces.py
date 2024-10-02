from tkinter import messagebox  # Import messagebox for confirmation
import cv2
import os
import csv
import mediapipe as mp


class FaceCapture:
    def __init__(self, camera_index=0, user_id=None, user_name=None):
        self.user_id = user_id
        self.user_name = user_name
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise Exception("Could not open video capture. Please check your camera.")
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if self.face_cascade.empty():
            raise Exception("Could not load haarcascades. Ensure the file exists.")
        self.names_file = 'names.csv'
        self.ensure_names_file()

        # Mediapipe face mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh()

    def ensure_names_file(self):
        """Ensure the names.csv file exists, if not, create it."""
        if not os.path.exists(self.names_file):
            with open(self.names_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['ID', 'Name'])  # Write the header

    def capture_faces(self):
        try:
            face_dir = f"Faces/{self.user_id}_{self.user_name}"
            os.makedirs(face_dir, exist_ok=True)

            # Add the new ID and name to names.csv
            with open(self.names_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([self.user_id, self.user_name])

            count = 0
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    messagebox.showwarning("Warning", "Failed to grab frame. Exiting...")
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert to grayscale for face detection
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(150, 150))

                for (x, y, w, h) in faces:
                    # Extract only the face region (without mesh for saving)
                    face = frame[y:y + h, x:x + w]
                    face = cv2.resize(face, (200, 200))  # Resize the face to a consistent size

                    # Save the clean face image (without face mesh)
                    count += 1
                    try:
                        cv2.imwrite(f"{face_dir}/{count}.jpg", face)
                    except Exception as e:
                        messagebox.showwarning("Warning", f"Error saving image {count}: {e}")

                    # Draw the face mesh on the display frame (but not on the saved image)
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self.face_mesh.process(rgb_frame)
                    if results.multi_face_landmarks:
                        for face_landmarks in results.multi_face_landmarks:
                            for landmark in face_landmarks.landmark:
                                x_landmark = int(landmark.x * frame.shape[1])
                                y_landmark = int(landmark.y * frame.shape[0])
                                cv2.circle(frame, (x_landmark, y_landmark), 1, (0, 255, 0), -1)

                    # Display the capture count on the frame (not the saved face)
                    cv2.putText(frame, f"Captured: {count}/100", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                    # Display the face region in a window for visualization
                    cv2.imshow("Captured Face", frame)

                if count >= 100:  # Capture 100 face images
                    break

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            # Show message after capture is complete
            messagebox.showinfo("Capture Complete", "Face capture completed successfully!")

        except Exception as e:
            messagebox.showwarning("Warning", f"An error occurred: {e}")

        finally:
            self.cap.release()
            cv2.destroyAllWindows()

    def delete_user_from_csv(self, user_id):
        """Delete the user with the given ID from the names.csv file."""
        try:
            # rows = []
            # Read all rows except the one with the given ID
            with open(self.names_file, 'r') as file:
                reader = csv.reader(file)
                rows = [row for row in reader if row[0] != user_id]

            # Write back the remaining rows to the file
            with open(self.names_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
        except Exception as e:
            messagebox.showwarning("Warning", f"Error deleting user from CSV: {e}")


if __name__ == "__main__":
    try:
        fc = FaceCapture(user_id=1, user_name="Cyber Bou")
        fc.capture_faces()
    except Exception as e:
        print(f"Failed to start face capture: {e}")
