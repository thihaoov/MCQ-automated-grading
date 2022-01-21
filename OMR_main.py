import cv2
import numpy as np
from numpy.lib import utils
import utlis

####################################
path = '1.jpg'
widthImg = 700
heightImg = 700
questions = 5
choices = 5
ans = [1,2,0,1,4]
webCamFeed = True
cameraNo = 0
####################################

cap = cv2.VideoCapture(cameraNo)
cap.set(10,150)

while True:
    if webCamFeed: success, img = cap.read()
    else: img = cv2.imread(path)

    # PREPROCESSING
    img = cv2.resize(img, (widthImg, heightImg))
    imgContours = img.copy()
    imgFinal = img.copy()
    imgBiggestContours = img.copy()
    imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray,(5,5),1) # Smoothing by Gaussian Blur
    imgCanny = cv2.Canny(imgBlur,10,50)

    try:
        # FINDING ALL CONTOURS
        contours, hierarchy = cv2.findContours(imgCanny,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(imgContours,contours,-1,(0,255,0),10)

        # FIND RECTANGLES
        rectCon = utlis.rectContour(contours)
        biggestContour = utlis.getConnerPoints(rectCon[0]) # return rect contour in order
        gradePoints = utlis.getConnerPoints(rectCon[1])
        # print(biggestContour.shape)

        if biggestContour.size != 0 and gradePoints.size != 0:
            cv2.drawContours(imgBiggestContours,biggestContour,-1,(0,255,0),20)
            cv2.drawContours(imgBiggestContours,gradePoints,-1,(255,0,0),20)

            biggestContour= utlis.reorder(biggestContour)
            gradePoints= utlis.reorder(gradePoints)

            # GETTING WARPPED IMAGES DOING PERSPECTIVE TRANSFORM
            pt1 = np.float32(biggestContour)
            pt2 = np.float32([[0,0], [widthImg,0], [0,heightImg], [widthImg,heightImg]])
            matrix = cv2.getPerspectiveTransform(pt1,pt2)
            imgWrapColored = cv2.warpPerspective(img,matrix,(widthImg,heightImg))

            ptG1 = np.float32(gradePoints)
            ptG2 = np.float32([[0,0], [325,0], [0,150], [325,150]])
            matrixG = cv2.getPerspectiveTransform(ptG1,ptG2)
            imgGradeDisplay = cv2.warpPerspective(img,matrixG,(325,150))
            # cv2.imshow("Grade",imgGradeDisplay)

            # APPLY THE THRESHOLD
            imgWarpGray = cv2.cvtColor(imgWrapColored,cv2.COLOR_BGR2GRAY)
            imgThresh = cv2.threshold(imgWarpGray,170,255,cv2.THRESH_BINARY_INV)[1]

            boxes = utlis.splitBoxes(imgThresh)
            # cv2.imshow("Test ",boxes[8])
            # print(cv2.countNonZero(boxes[1]),cv2.countNonZero(boxes[2]))

            # GETTING NON ZERO PIXEL COUNTS OF EACH BOXES
            myPixelVal = np.zeros((questions,choices))
            countCol = 0
            countRow = 0
            for image in boxes:
                totalPixels = cv2.countNonZero(image)
                myPixelVal[countRow][countCol] = totalPixels
                countCol += 1
                if countCol == choices : countRow += 1; countCol = 0
            # print(myPixelVal)

            # FINDING INDEX VALUES OF THE MARKINGS
            myIndex = []
            for x in range(0,questions):
                arr = myPixelVal[x]
                # print(arr)
                myIndexVal = np.where(arr==np.amax(arr)) # get index where max non zero count exist
                # print(myIndexVal[0])
                myIndex.append(myIndexVal[0][0])
            # print(myIndex)

            # GRADING
            grading = []
            for x in range(0,questions):
                if ans[x] == myIndex[x]:
                    grading.append(1)
                else: grading.append(0)
            # print(grading)
            score = sum(grading)/questions * 100 # FINAL GRADE
            print(score)

            # DISPLAY ANSWERS
            imgResult = imgWrapColored.copy()
            imgResult = utlis.showAnswers(imgResult, myIndex, grading, ans, questions, choices)

            imRawDrawing = np.zeros_like(imgWrapColored)
            imRawDrawing = utlis.showAnswers(imRawDrawing, myIndex, grading, ans, questions, choices)

            invMatrix = cv2.getPerspectiveTransform(pt2,pt1)
            imgInvWarp = cv2.warpPerspective(imRawDrawing,invMatrix,(widthImg,heightImg))

            imgRawGrade =  np.zeros_like(imgGradeDisplay)
            cv2.putText(imgRawGrade,str(int(score))+"%",(70,100),cv2.FONT_HERSHEY_COMPLEX,3,(0,255,255),3)
            invMatrixG = cv2.getPerspectiveTransform(ptG2,ptG1)
            imgInvGradeDisplay = cv2.warpPerspective(imgRawGrade,invMatrixG,(widthImg,heightImg))

            imgFinal = cv2.addWeighted(imgFinal,1,imgInvWarp,1,0)
            imgFinal = cv2.addWeighted(imgFinal,1,imgInvGradeDisplay,1,0)


        imgBlank = np.zeros_like(img)
        imageArray = ([img,imgGray,imgBlur,imgCanny],
                    [imgContours,imgBiggestContours,imgWrapColored,imgThresh],
                    [imgResult,imRawDrawing,imgInvWarp,imgFinal])
    except:
        imgBlank = np.zeros_like(img)
        imageArray = ([img,imgGray,imgBlur,imgCanny],
                    [imgBlank,imgBlank,imgBlank,imgBlank],
                    [imgBlank,imgBlank,imgBlank,imgBlank])

    lables = [["Original","Gray","Blur","Canny"],
            ["Contours","Biggest Contours","Warpped","Threshold"],
            ["Result","RawDrawing","Inv Warp","Final"]]

    imgStacked = utlis.stackImages(imageArray,0.3,lables)

    cv2.imshow("Final Result", imgFinal)
    cv2.imshow("Stacked", imgStacked)
    if cv2.waitKey(1) & 0xFFF == ord('s'):
        cv2.imwrite("FinalResult.jpg",imgFinal)
        cv2.waitKey(300)

