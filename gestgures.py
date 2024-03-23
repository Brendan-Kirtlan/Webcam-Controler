import cv2
import mediapipe as mp
from deepface import DeepFace
import keyboard
from time import sleep
import threading
import math

#The average distances found for my hand
c_shape = [5.807196336837074, 8.48686494240277, 8.683824381319946, 8.770978026367676, 8.755430636592692]
c_pairs = [4,0,8,0,12,0,16,0,20,0]
#avg pinky length for my samples, can only be used at same distance of samples
pinky_length = 0.03433480395568249
open_cooldown = 0
attack_cooldown = 0
roll_cooldown = 0

def press_keys(right, left, emotion, open, last_key, c_flag):
    global open_cooldown
    global attack_cooldown
    global roll_cooldown
    key = ''
    #held keys
    if right == 1:
        key = 'w'
    elif right == 2:
        key = 'a'
    elif right == 3:
        key = 's'
    elif right == 4:
        key = 'd'
    
    #releases last held key
    if(key != last_key):
        if last_key != '':
            keyboard.release(last_key)
        if key != '':
            keyboard.press(key)
    
    
    #tapped keys
    if open and open_cooldown == 0:
        open_cooldown = 30
        open_thread = threading.Thread(target=press_key_thread('q'))
        open_thread.start()
    
    if open_cooldown > 0:
        open_cooldown -= 1
    if attack_cooldown > 0:
        attack_cooldown -= 1
    if roll_cooldown > 0:
        roll_cooldown -= 1

    if left == 2:
        c_thread = threading.Thread(target=press_key_thread('e'))
        c_thread.start()
    elif left == 1 and roll_cooldown == 0:
        roll_cooldown = 10
        left_thread = threading.Thread(target=press_key_thread(' '))
        left_thread.start()
    elif left == 3:
        left_thread = threading.Thread(target=press_key_thread('r'))
        left_thread.start()
    if emotion and attack_cooldown == 0 and emotion== "angry":
        attack_cooldown = 12
        emotion_thread = threading.Thread(target=press_key_thread('l'))
        emotion_thread.start()
        
    
    return key

def press_key_thread(c):
    keyboard.press(c)
    sleep(0.1)
    keyboard.release(c)

def release_keys(keys):
    for key in keys:
        keyboard.release(key)

def detect_emotion(frame):
    try:
        result = DeepFace.analyze(frame, actions=['emotion'])

        if isinstance(result, list):
            result = result[0]
            #print(result)
        #dominant_emotion = result['dominant_emotion']
        #messing with threshold to get more cosistent results
        if(result['emotion']['angry'] > 75 and result['dominant_emotion'] == 'angry'):
            return 'angry'
        elif result['dominant_emotion'] == 'angry':
            return 'neutral'
        else:
            return result['dominant_emotion']

    except ValueError as e:
        print("No face detected.")
        return "Not Available"

def is_mouth_open(frame, mesh_results, mouth_open_threshold=25):

    if mesh_results.multi_face_landmarks:
        landmarks = mesh_results.multi_face_landmarks[0].landmark
                
        #get dist between upper and lower lips
        upper_lip_y = int(landmarks[13].y * frame.shape[0])  #upper lip landmark
        lower_lip_y = int(landmarks[14].y * frame.shape[0])  #lower lip landmark
        lip_distance = lower_lip_y - upper_lip_y

        return lip_distance > mouth_open_threshold

    return False

def count_fingers(hand_landmarks):
    #done with an array in case individual fingers wanted to be detected for
    finger_up = [0] * 5

    #inconsistent cause thumb points sideways
    # Thumb
    #if hand_landmarks[4].y > hand_landmarks[3].y:
    #    finger_up[0] = 1

    #Index finger
    if hand_landmarks[8].y < hand_landmarks[6].y:
        finger_up[1] = 1

    #Middle finger
    if hand_landmarks[12].y < hand_landmarks[10].y:
        finger_up[2] = 1

    #Ring finger
    if hand_landmarks[16].y < hand_landmarks[14].y:
        finger_up[3] = 1

    #Pinky
    if hand_landmarks[20].y < hand_landmarks[18].y:
        finger_up[4] = 1

    return sum(finger_up)

def detect_gesture(hand_landmarks):
    tolerance = 1
    i = 0
    #live pinky length
    pink_test = math.sqrt((hand_landmarks[20].x - hand_landmarks[19].x)**2 + (hand_landmarks[20].y - hand_landmarks[19].y)**2 + (hand_landmarks[20].z - hand_landmarks[19].z)**2)
    while i < len(c_pairs) - 1:
        #uses c pairs array to determine which landmarks to calculate distance between
        dist = math.sqrt((hand_landmarks[c_pairs[i]].x - hand_landmarks[c_pairs[i+1]].x)**2 + (hand_landmarks[c_pairs[i]].y - hand_landmarks[c_pairs[i+1]].y)**2 + (hand_landmarks[c_pairs[i]].z - hand_landmarks[c_pairs[i+1]].z)**2)
        #print(dist)
        #dist = dist / pinky_length
        dist = dist / pink_test
        #print(dist)
        if(abs(dist - c_shape[int(i/2)]) > tolerance):
            return False
        i += 2
    return True

def write_to_file(file_path, content):
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"Content successfully written to {file_path}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    mouth_cooldown = 0
    last_key = ''
    framesPassed = 10
    out_file_num = 0
    emotion = ""
    c_flag = False
    mouth_open = False
    
    #Initializations
    cap = cv2.VideoCapture(0)
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands()
    mp_face_mesh = mp.solutions.face_mesh

    mp_drawing = mp.solutions.drawing_utils
    face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5, max_num_faces=1)

    left_hand_fingers_up = 0
    right_hand_fingers_up = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb_frame)
        mesh_results = face_mesh.process(rgb_frame)


        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                landmarks = hand_landmarks.landmark
                fingers_up_count = count_fingers(landmarks)

                #check for left or right hand
                if hand_landmarks.landmark[mp_hands.HandLandmark.WRIST.value].x < 0.5:
                    right_hand_fingers_up = fingers_up_count
                else:
                    left_hand_fingers_up = fingers_up_count
                    if left_hand_fingers_up == 4:
                        c_flag = detect_gesture(landmarks)
                    #dist = math.sqrt((landmarks[c_pairs[4]].x - landmarks[c_pairs[0]].x)**2 + (landmarks[c_pairs[4]].y - landmarks[c_pairs[0]].y)**2 + (landmarks[c_pairs[4]].z - landmarks[c_pairs[0]].z)**2)
                    #rounded_dist = round(dist, 2)

                    #cv2.putText(frame, f"Thumb to palm dist: {rounded_dist}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                cv2.putText(frame, f"Left Hand Fingers Up: {left_hand_fingers_up}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(frame, f"Right Hand Fingers Up: {right_hand_fingers_up}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(frame, f"C Shape: {c_flag}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                
                
        if(framesPassed == 20):
            emotion = detect_emotion(frame)
            framesPassed = 0
        else:
            framesPassed += 1


        mouth_open = is_mouth_open(rgb_frame, mesh_results)
        
        cv2.putText(frame, f"Current emotion: {emotion}", (10, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Mouth open: {mouth_open}", (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Hand Gesture Recognition', frame)
        
        #uncomment this to make the program press the keys
        #last_key = press_keys(right_hand_fingers_up, left_hand_fingers_up, emotion, mouth_open, last_key, c_flag)
        

        #quit with m
        if cv2.waitKey(1) & 0xFF == ord('m'):
            break
        
        i = 0
        
        #Saving the position of hands to file
        if cv2.waitKey(1) & 0xFF == ord('u'):
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    landmarks = hand_landmarks.landmark
                    all = ''
                    if hand_landmarks.landmark[mp_hands.HandLandmark.WRIST.value].x >= 0.5:
                        for trip in landmarks:
                            s = str(landmarks[i].x) + ',' + str(landmarks[i].y) + ',' + str(landmarks[i].z)
                            #print(s)
                            i+=1
                            all += s + '\n'
                        #need directory path
                        #write_to_file(r'' + str(out_file_num) + '.txt', all)
                        out_file_num += 1

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
