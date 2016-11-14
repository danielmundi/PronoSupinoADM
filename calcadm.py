import sys
import csv
import math
import argparse
import numpy as np
from numpy.linalg import norm
import matplotlib.pyplot as plt
import scipy.signal as signal
import peakutils


def defvec(end, begin):
    v = (end-begin)/norm(end-begin)
    return v


def crossnorm(vec1, vec2):
    vecr = np.cross(vec1, vec2)
    vecr = vecr/norm(vecr)
    return vecr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="The path for the TSV file")

    args = parser.parse_args()
    path = args.path

    markers_order = ["AC", "EL", "EM", "RS", "US"]
    angles = []

    fig = plt.figure()
    sp = fig.add_subplot(111)

    with open(path, "r") as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter="\t")

        for line in tsvreader:
            print(line[1])
            if len(line) == 6:
                if line[0] == "MARKER_NAMES":
                    markers = line[1:]

                # Find the indices according to the expected order
                # Considering the markers can be on any order in the file
                indices = [markers.index(m) for m in markers_order]
                break
            elif len(line) > 6:
                sys.exit(1)

        # print(markers)
        # print(markers_order)
        # print(indices)
        # print([m for (i,m) in sorted(zip(indices, markers))])

        points = []

        for line in tsvreader:
            line = list(map(float, line))
            # Read the 3D position of each marker from the current line
            AC, EL, EM, RS, US = (
                np.asarray(line[3*indices[i]: 3*indices[i]+3]) for i in range(5)
            )

            # print(AC, EL, EM, RS, US)
            points.append((AC, EL, EM, RS, US))

    for AC, EL, EM, RS, US in points:
        epi_medium = np.asarray([(x+y)/2 for x,y in zip(EL, EM)])
        # print(epi_medium)

        #US = np.asarray([x1 - (x2-x1)*0.1 for x1,x2 in zip(US, RS)])

        Of = US
        Yf = defvec(epi_medium, US)
        Xf = crossnorm(defvec(epi_medium, RS), defvec(epi_medium, US))
        Zf = crossnorm(Xf, Yf)

        Oh = AC
        Yh = defvec(AC, epi_medium)
        Zh = crossnorm(Yf, Yh)
        Xh = crossnorm(Yh, Zh)

        e1 = Zh
        e3 = Yf
        e2 = crossnorm(e3, e1)

        fj = Xf
        lj = Yf
        tj = crossnorm(lj, fj)

        if (np.dot(np.cross(e3, e1), tj) < 0 and
                np.dot(np.cross(np.cross(e3, e1), e3), fj)) > 0:
            e2 = -e2

        angle1 = math.copysign(math.acos(np.dot(e2, Xh)), np.dot(e2, Yh))
        angle3 = math.copysign(math.acos(np.dot(e2, tj)), np.dot(e2, fj))
        #angle = math.copysign(math.acos(np.dot(crossnorm(e1,e2), Xf)), np.dot(e1, e3))

        angles.append(math.degrees(angle3))

    angles = np.asarray(angles)
    angles_neg = -1*angles


    # y = angles[30:3.2*120]
    # y = y - np.full(len(y), np.mean(y))


    x = np.arange(0, len(angles)/120, 1/120)
    x = x[:len(angles)]

    # f, p_spec = signal.welch(y, 120, scaling='spectrum')
    # #plt.semilogy(f, p_spec)
    # plt.plot(x,y)
    # plt.xlabel('Tempo (s)')
    # plt.ylabel('Amplitude (graus)')
    # plt.grid()
    # plt.show()
    # return

    #angle_start = np.mean(angles[:120])
    #angles = [x - angle_start for x in angles]
    #print(angle_start)

    #max_angle, min_angle = maxmin(angles)
    #print(max_angle[1] - min_angle[1])

    imax = peakutils.indexes(angles, thres=0.1, min_dist=240)
    imin = peakutils.indexes(angles_neg, thres=30/max(angles_neg), min_dist=2*120)

    media_prono = sum(angles[i] for i in imax)/len(imax)
    media_supino = sum(angles[i] for i in imin)/len(imin)
    print((media_prono, media_supino))

    sp.plot(x, angles)

    for peak in imax:
        sp.annotate("{:.0f}°".format(angles[peak]), xy=(peak/120,angles[peak]), xycoords='data',
            xytext=(-30, 15), textcoords='offset points',
            arrowprops=dict(arrowstyle="->"))

    for peak in imin:
        sp.annotate("{:.0f}°".format(angles[peak]), xy=(peak/120,angles[peak]), xycoords='data',
            xytext=(-50, -5), textcoords='offset points',
            arrowprops=dict(arrowstyle="->"))

    #sp.annotate("Max. pronation {:.0f}°".format(max_angle[1]), xy=max_angle, xycoords='data',
    #        xytext=(-110, 10), textcoords='offset points',
    #        arrowprops=dict(arrowstyle="->"))
    #sp.annotate("Max. supination {:.0f}°".format(min_angle[1]), xy=min_angle, xycoords='data',
    #        xytext=(-140, 10), textcoords='offset points',
    #        arrowprops=dict(arrowstyle="->"))

    plt.xlabel("Tempo (s)")
    plt.ylabel("Ângulo (graus)")

    #sp.grid()
    #plt.show()
    #plt.draw()


def maxmin(x):
    max = float('-Inf')
    max_id = -1
    min = float('Inf')
    min_id = -1
    for i, a in enumerate(x):
        if a > max:
            max = a
            max_id = i
        elif a < min:
            min = a
            min_id = i

    return ((max_id/120, max), (min_id/120, min))


if __name__ == "__main__":
    main()
