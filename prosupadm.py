import csv
import os.path
import math
import numpy as np
from numpy.linalg import norm
import matplotlib.pyplot as plt
import peakutils


class ProSupADM():
    ''' Calculate forearm's axial rotation from optic
    motion capture system's data '''

    markers_order = ["AC", "EL", "EM", "RS", "US"]

    def __init__(self, path=None):
        self.path = path
        self.initialize()

    def analyse(self, path=None, imagePath=None):

        if self.angles is not None:
            self.initialize(path)

        ok = self.processFile(path)
        if not ok:
            return False

        ok = self.calculateAngles()
        if not ok:
            return False

        ok = self.showPlot(imagePath)
        if not ok:
            return False

    def processFile(self, path=None):
        if not self.checkPath(path):
            return False

        with open(self.path, "r") as tsvfile:
            tsvreader = csv.reader(tsvfile, delimiter="\t")
            
            for line in tsvreader:
                if line[0] == "NO_OF_FRAMES":
                    self.total_frames = int(line[1])
                    self.angles = np.empty(self.total_frames)
                elif line[0] == "FREQUENCY":
                    self.frequency = int(line[1])
                elif line[0] == "NO_OF_MARKERS":
                    if int(line[1]) != 5:
                        print("Erro: Número de marcadores " \
                            "incorretos. 5 marcadores esperados, " \
                            "{} encontrados no arquivo. Verifque " \
                            "exportação do software QTM.".format(
                                int(line[1])))
                        return False
                elif line[0] == "MARKER_NAMES":
                    if len(line) > 6:
                        print("Erro: Cabeçalho do arquivo TSV em " \
                            "formato incorreto.")
                        return False
                    markers = line[1:]

                    # Find the indices according to the expected 
                    # order. Considering the markers can be on 
                    # any order in the file
                    indices = [markers.index(m) for m
                                        in self.markers_order]
                    break
            
            if len(markers) < 5:
                print("Erro: Arquivo com menos marcadores do que " \
                    "o esperado.")
                return False

            for line in tsvreader:
                if len(line) != len(markers)*3:
                    print("Erro: Incosistênia nos vetores de " \
                        "posição dos marcadores.")
                    return False

                line = list(map(float, line))
                # Read the 3D position of each marker from 
                # the current line
                AC, EL, EM, RS, US = (
                    np.asarray(line[3*indices[i]: 3*indices[i]+3])
                                                    for i in range(5)
                )

                self.points.append((AC, EL, EM, RS, US))

            return True

    def calculateAngles(self):
        if len(self.points) == 0:
            print("Erro: Chame 'processFile()' antes de calcular " \
                "os ângulos.")
            return False
        if self.frequency == 0:
            self.frequency = 120
            print("Atenção: Frequência de captura não definida no " \
                "cabeçalho. Utilizando o padrão de 120 Hz.")

        for i, (AC, EL, EM, RS, US) in enumerate(self.points):
            epi_medium = np.asarray([(x+y)/2 for x,y in zip(EL, EM)])

            # Defining forearm coordinate system
            Of = US
            Yf = self.defineVector(epi_medium, US)
            Xf = self.crossNorm(self.defineVector(epi_medium, RS),
                                self.defineVector(epi_medium, US))
            Zf = self.crossNorm(Xf, Yf)

            # Defining humerus coordinate system
            Oh = AC
            Yh = self.defineVector(AC, epi_medium)
            Zh = self.crossNorm(Yf, Yh)
            Xh = self.crossNorm(Yh, Zh)

            e1 = Zh
            e3 = Yf
            e2 = self.crossNorm(e3, e1)

            fj = Xf
            lj = Yf
            tj = self.crossNorm(lj, fj)

            if (np.dot(np.cross(e3, e1), tj) < 0 and
                    np.dot(np.cross(np.cross(e3, e1), e3), fj)) > 0:
                e2 = -e2

            angle1 = math.copysign(
                math.acos(np.dot(e2, Xh)),
                np.dot(e2, Yh)
            )
            angle3 = math.copysign(
                math.acos(np.dot(e2, tj)),
                np.dot(e2, fj)
            )

            self.angles[i] = math.degrees(angle3)

        self.angles = np.asarray(self.angles)
        # Need to reverse angles to find supination peaks
        angles_neg = -1*self.angles

        self.x = np.arange(0, len(self.angles)/120, 1/120)
        self.x = self.x[:len(self.angles)]

        # Find pronation peaks
        self.id_prono_peaks = peakutils.indexes(self.angles,
            thres=0.2, min_dist=240)
        # Find supination peaks
        self.id_supino_peaks = peakutils.indexes(angles_neg,
            thres=0.3, min_dist=2*120)

        # Calculate mean for the pronation peaks
        self.adm_pronation = sum(self.angles[i] for i
            in self.id_prono_peaks)/len(self.id_prono_peaks)
        # Calculate mean for the supination peaks
        self.adm_supination = sum(self.angles[i] for i
            in self.id_supino_peaks)/len(self.id_supino_peaks)

        self.adm_total = self.adm_pronation-self.adm_supination

        print("ADM supinação: {:.1f} graus".format(
            self.adm_pronation))
        print("ADM pronação: {:.1f} graus".format(
            self.adm_supination))
        print("ADM total: {:.1f}".format(
            self.adm_total))

        return True

    def showPlot(self, imagePath=None):
        if len(self.angles) == 0 or len(self.angles) != len(self.x):
            print("Erro: Execute as funções 'processFile' e " \
                "'calculateAngles' antes de imprimir o gráfico.")
            return False

        fig = plt.figure()
        sp = fig.add_subplot(111)

        sp.plot(self.x, self.angles)

        for peak in self.id_prono_peaks:
            sp.annotate("{:.0f}°".format(self.angles[peak]), 
                xy=(peak/120,self.angles[peak]), xycoords='data',
                xytext=(-30, 15), textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))

        for peak in self.id_supino_peaks:
            sp.annotate("{:.0f}°".format(self.angles[peak]), 
                xy=(peak/120,self.angles[peak]), xycoords='data',
                xytext=(-50, -5), textcoords='offset points',
                arrowprops=dict(arrowstyle="->"))

        plt.xlabel("Tempo (s)")
        plt.ylabel("Ângulo (graus)")

        sp.grid()

        if imagePath is None:
            plt.show()
            plt.draw()
        else:
            plt.savefig(imagePath)

        return True

    def defineVector(self, end, begin):
        return (end-begin)/norm(end-begin)

    def crossNorm(self, vec1, vec2):
        vecr = np.cross(vec1, vec2)
        vecr = vecr/norm(vecr)
        return vecr

    def checkPath(self, path):
        if path is None:
            print("Erro: Nenhum arquivo selecionado")
            return False
        elif not os.path.exists(path):
            print("Erro: Arquivo não existente")
            return False
        elif path.rsplit('.', 1)[1] not in ['tsv', 'TSV']:
            print("Erro: Extensão do arquivo deve ser '.tsv'")
            return False
        else:
            self.path = path
            return True

    def initialize(self, path=None):
        if path is not None:
            self.path = path
        self.total_frames = 0
        self.frequency = 0
        self.angles = None
        self.x = None
        self.id_prono_peaks = []
        self.id_supino_peaks = []
        self.points = []
        self.adm_pronation = 0
        self.adm_supination = 0
        self.adm_total = 0
