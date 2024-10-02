from tkinter import messagebox  # Import messagebox for confirmation
import cv2
import os
import numpy as np

class Trainer:
    def __init__(self):
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.faces_dir = "Faces/"
        self.model_file = 'trainer.yml'

    def train_faces(self):
        faces, ids = [], []
        if not os.path.exists(self.faces_dir):
            # print(f"Directory {self.faces_dir} does not exist. No faces to train.")
            return

        for dir_name in os.listdir(self.faces_dir):
            user_id = int(dir_name.split('_')[0])
            dir_path = os.path.join(self.faces_dir, dir_name)

            for img_name in os.listdir(dir_path):
                img_path = os.path.join(dir_path, img_name)
                gray_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

                if gray_img is None:
                    messagebox.showwarning("Warning", f"Could not read image {img_path}. Skipping...")
                    continue

                faces.append(gray_img)
                ids.append(user_id)

        if len(faces) == 0:
            messagebox.showerror("Error", "No valid face data found for training.")
            return

        try:
            messagebox.showinfo("Completed", f"Training on {len(faces)} face images.")
            self.recognizer.train(faces, np.array(ids))
            self.save_model()
        except Exception as e:
            messagebox.showerror("Error", f"Error during training: {e}")

    def save_model(self):
        """Save the trained model to file."""
        try:
            self.recognizer.save(self.model_file)
            messagebox.showinfo("Saved", f"Model trained and saved as {self.model_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving model: {e}")

if __name__ == "__main__":
    trainer = Trainer()
    trainer.train_faces()
