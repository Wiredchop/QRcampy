from qrcam import cam_params,QRcam
import cv2, time

if  __name__ == "__main__":
    #Create default parameters
    params = cam_params(annotate=False)
    my_cam = QRcam(params)
    my_cam.start_camera()
    while not my_cam.id_found:
        image = my_cam.get_image()
        cv2.imshow('',image)
        if(cv2.waitKey(1) == ord("q")):
            break
    print(f'data found, it is {my_cam.ID} ')