import math
import xlwt

n1 = [0,0]
n2 = [1,1]
n3 = [1,-1]
n4 = [0,0]
co = ((n2[0]-n1[0]) * (n4[0]-n3[0]) + (n2[1]-n1[1]) * (n4[1]-n3[1])) / (math.sqrt(math.pow(n2[0]-n1[0], 2) + math.pow(n2[1]-n1[1], 2)) * math.sqrt(math.pow(n4[0]-n3[0], 2) + math.pow(n4[1]-n3[1], 2)))
print(co)
re = math.acos(co)
print(re/math.pi)


overhead = [1,2,3,4,555,6]
f = xlwt.Workbook()
sheet1 = f.add_sheet(u'sheet1', cell_overwrite_ok=True)
i = 0
for j in range(len(overhead)):
    sheet1.write(j, i, overhead[j])
i = i + 1
overhead = [1,2,3,4,555,777]
for j in range(len(overhead)):
    sheet1.write(j, i, overhead[j])
f.save("xxxxxx.xls")