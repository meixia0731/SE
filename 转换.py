def Converter(number,index,direction,sign):
#index为该数据位宽,number为待转换数据,direction为转换方向(1为十进制转机器码，2为机器码转十进制),sign为输入或输出的机器码是否带符号(1为带符号，2为不带符号),
    result = []
    result1 = []
    if (direction == 1):#十进制转机器码
        if sign ==1:
            if index == 16 and (number > 32767 or number < -32768):
                print('MAX int16 is -32768~ +32767')
                return
            elif index == 32 and (number > 2147483647 or number < -2147483648):
                print('MAX int32 is -2,147,483,648 ~ +2,147,483,647')
                return
            elif index == 64 and (number > 9223372036854775807  or number < -9223372036854775808):
                print('MAX int64 is -9,223,372,036,854,775,808 ~ +9,223,372,036,854,775,807 ')
                return
            if(number >= 0):
                b=bin(number)
                b = '0' * (index+2 - len(b)) + b
            else:
                b=2**(index)+number
                b=bin(b)
                b = '1' * (index+2 - len(b)) + b    #注意这里算出来的结果是补码
            b=b.replace("0b",'')
            b=b.replace('-','')
            for i in range(int(index/8)):
                result.append(int(b[0:8],2))
                b=b[8:]
            for i in range(int(len(result)/2)):
                result1.append(result[0]*256+result[1])
                result = result[2:]
            return result1
        elif sign ==2:
            if(number >= 0):
                b=bin(number)
                b = '0' * (index+2 - len(b)) + b
                print(b)
            else:
                print('Input must be positive')
                return
            b=b.replace("0b",'')
            print(b)
            for i in range(int(index/8)):
                result.append(int(b[0:8],2))
                b=b[8:]
            print(result)
            for i in range(int(len(result)/2)):
                result1.append(result[0]*256+result[1])
                result = result[2:]
            print(result1)
            return result1          
    elif(direction==2):#机器码转十进制
        j=''
        if sign ==2:
            for i in range(len(number)):
                j = j + '{:0>4x}'.format(number[i])
                print(j)
            j=int(j,16)
            return j
        elif sign ==1:
            for i in range(len(number)):
                j = j + '{:0>4x}'.format(number[i])
            j=int(j,16)
            if(number[0]>127):#如果首位是1
                j=-(2**index-j)
                return j
            else:
                return j

