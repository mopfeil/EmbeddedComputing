import glob
import pylab



def loadData(fileName):
    inFile = open(fileName, 'r')    #read-only mode

    #Define 2 empty lists, used to store the data in the file
    x = []
    y = []
    for line in inFile:
        if "#" not in line:
            trainingSet = line.split(',')   #   Remove separator','
            x.append(float(trainingSet[0])) #   The first column of data
            y.append(float(trainingSet[1])) #   The second column of data


    return (x, y)

#Draw the data in the file
def plotData(x, y, filename):

    pylab.title('SpeedSetting:' + str(filename) )
    pylab.plot(x, y, 'ko')      #'ko' indicates that the type of point is a black solid dot
    pylab.xlabel('Time ')
    pylab.ylabel('Distance')
    pylab.show()        #Let the drawn image be displayed on the screen


txt_files = glob.glob("*.txt")
print(txt_files)

for i in txt_files:
    print(i)
    filename = i.rsplit('.', 1)[0]  # Extract file name for Labelling Plot
    (x, y, ) = loadData(i)
    print(x, y)
    plotData(x, y, filename)

