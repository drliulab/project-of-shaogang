# -*- coding:utf-8 -*-
import os.path
import cv2
import shutil
from moviepy.editor import *
import argparse
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess
import time

import tkinter
import tkinter.messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
from time import sleep
from tkinter import IntVar, StringVar

import pymssql
import math

class MyGui:
    def __init__(self, framesdir, annsdir, mark_cls,drop):
        # 创建tkinter主窗口
        self.labelcnt = 0
        self.labelsum = 0
        self.labels = {}
        for d in os.listdir(framesdir):
            for each_frame in os.listdir(framesdir + d):
                self.labels[self.labelsum] = {}
                self.labels[self.labelsum]['framepath'] = framesdir + d + '/' + each_frame
                self.labels[self.labelsum]['annpath'] = annsdir + d + '/' + each_frame[:each_frame.rfind('.')] + '.txt'
                self.labels[self.labelsum]['dropout'] = 0
                self.labelsum += 1
        print("labelsum : " + str(self.labelsum))
        print("the last one :" + self.labels[self.labelsum - 1]['framepath'])
        self.root = tkinter.Tk()
        # 指定主窗口位置与大小
        self.root.geometry('1900x980+10+10')
        # 不允许改变窗口大小
        self.root.resizable(False, False)
        self.X = tkinter.IntVar(value=0)
        self.Y = tkinter.IntVar(value=0)
        self.selectPosition = None
        if mark_cls == "zhongkong":
            self.idtext = {'0': 'norm', '1': 'look at phone', '2': 'sleep'}
        elif mark_cls == "zhaxian":
            self.idtext = {'0': 'person', '1': ' ', '2': ' '}
        self.idlist = []
        self.lines = []

        self.outlog = StringVar()
        self.outlog.set("读取成功！")
        self.text_outlog = tkinter.Label(self.root, font="Helvetica 15 bold", textvariable=self.outlog, state='normal',
                                         width=3, bg="#4A708B", fg="#8B1A1A",
                                         disabledforeground="yellow", highlightbackground="black",
                                         highlightcolor="red", highlightthickness=1, bd=0)
        self.text_outlog.place(x=1710, y=50 + 35 * 21, width=180, height=150)

        # canvas尺寸
        screenWidth = 1703  # root.winfo_screenwidth()
        screenHeight = 958  # root.winfo_screenheight()
        # 创建顶级组件容器
        # self.top = tkinter.Toplevel(self.root,width=screenWidth,height=screenHeight)
        # 不显示最大化、最小化按钮
        # self.root.overrideredirect(True)

        self.canvas = tkinter.Canvas(self.root, bg='white', width=screenWidth, height=screenHeight)
        im = Image.open(self.labels[self.labelcnt]['framepath'])
        im = im.resize((1703, 958))
        self.draw_bbox(im)
        self.image = ImageTk.PhotoImage(im)
        self.canvas.create_image(0, 0, anchor='nw', image=self.image)
        self.root.title(self.labels[self.labelcnt]['framepath'])

        def but_preCaptureClick():
            if (self.labelcnt == 0):
                return
            self.labelcnt -= 1
            if (self.labels[self.labelcnt]['dropout']):
                temp = self.labelcnt + 1
                while self.labelcnt >= 0 and self.labels[self.labelcnt]['dropout']:
                    self.labelcnt -= 1
                if (self.labelcnt < 0):
                    self.labelcnt = temp
                    return
            ims = Image.open(self.labels[self.labelcnt]['framepath'])
            ims = ims.resize((1703, 958))
            self.draw_bbox(ims)
            self.image = ImageTk.PhotoImage(ims)
            self.canvas.create_image(0, 0, anchor='nw', image=self.image)
            self.root.title(self.labels[self.labelcnt]['framepath'])
            print("self.labelcnt : " + str(self.labelcnt))

        def but_afterCaptureClick():
            if (self.labelcnt == self.labelsum):
                return

            self.labelcnt += 1
            if (self.labels[self.labelcnt]['dropout']):
                temp = self.labelcnt - 1
                while self.labelcnt < self.labelsum and self.labels[self.labelcnt]['dropout']:
                    self.labelcnt += 1
                if (self.labelcnt == self.labelsum):
                    self.labelcnt = temp
                    return
            ims = Image.open(self.labels[self.labelcnt]['framepath'])
            ims = ims.resize((1703, 958))
            self.draw_bbox(ims)
            self.image = ImageTk.PhotoImage(ims)
            self.canvas.create_image(0, 0, anchor='nw', image=self.image)
            self.root.title(self.labels[self.labelcnt]['framepath'])
            print("self.labelcnt : " + str(self.labelcnt))

        def but_dropoutCaptureClick():
            a = tkinter.messagebox.askokcancel('警告', 'dropout不可复原，确认？')

            if (a is False):
                return

            src = self.labels[self.labelcnt]['framepath']
            name = src[src.rfind('frames') + 6:]
            if not os.path.exists(drop + 'wait_frames'):
                os.makedirs(drop+'wait_frames')
            folder = drop + 'wait_frames' + name
            folder = folder[:folder.rfind('/')]
            if not os.path.exists(folder):
                os.mkdir(folder)
            os.rename(src, drop + 'wait_frames' + name)

            src = self.labels[self.labelcnt]['annpath']
            name = src[src.rfind('anns') + 4:]
            if not os.path.exists(drop + 'wait_anns'):
                os.makedirs(drop+'wait_anns')
            folder = drop + 'wait_anns' + name
            folder = folder[:folder.rfind('/')]
            if not os.path.exists(folder):
                os.mkdir(folder)
            os.rename(src, drop + 'wait_anns' + name)
            self.labels[self.labelcnt]['dropout'] = 1
            but_afterCaptureClick()

        self.canvas.bind('<Button-1>', self.onLeftButtonDown)
        self.canvas.bind('<B1-Motion>', self.onLeftButtonMove)
        self.canvas.bind('<ButtonRelease-1>', self.onLeftButtonUp)
        self.canvas.place(x=0, y=0)  # pack(fill=tkinter.Y,expand=tkinter.YES)

        self.but_dropout = tkinter.Button(self.root, text="Drop out", command=but_dropoutCaptureClick)
        self.but_dropout.place(x=1710, y=0, width=80, height=20)
        self.but_pre = tkinter.Button(self.root, text="<- Prev", command=but_preCaptureClick)
        self.but_pre.place(x=1710, y=25, width=80, height=20)
        self.but_after = tkinter.Button(self.root, text="After ->", command=but_afterCaptureClick)
        self.but_after.place(x=1795, y=25, width=80, height=20)

        # 启动消息主循环
        self.root.mainloop()

    # 鼠标左键按下的位置
    def onLeftButtonDown(self, event):
        self.X.set(event.x)
        self.Y.set(event.y)
        # 开始画框的标志
        self.sel = True

    # 鼠标左键移动，显示选取的区域
    def onLeftButtonMove(self, event):
        if not self.sel:
            return
        global lastDraw
        try:
            # 删除刚画完的图形，否则鼠标移动的时候是黑乎乎的一片矩形
            self.canvas.delete(lastDraw)
        except Exception as e:
            pass
        lastDraw = self.canvas.create_rectangle(self.X.get(), self.Y.get(), event.x, event.y, outline='yellow')

    # 获取鼠标左键抬起的位置，记录区域
    def onLeftButtonUp(self, event):
        self.sel = False
        try:
            self.canvas.delete(lastDraw)
        except Exception as e:
            pass
        sleep(0.1)
        print(event.x, event.y)
        upx = event.x if event.x < 1703 else 1703
        upy = event.y if event.y < 958 else 958
        upx = upx if upx > 0 else 0
        upy = upy if upy > 0 else 0
        myleft, myright = sorted([self.X.get(), upx])
        mytop, mybottom = sorted([self.Y.get(), upy])
        self.selectPosition = (myleft, myright, mytop, mybottom)
        print("选择区域bbox：xmin:" + str(self.selectPosition[0]) + ' ymin:' + str(
            self.selectPosition[2]) + ' xmax:' + str(self.selectPosition[1]) + ' ymax:' + str(
            self.selectPosition[3]))
        self.but_addCaptureClick()

    def but_confirmCaptureClick(self, event):
        # 如果修改了文本框的值，把新值写会标注文件对应行
        the_butt = event.widget
        the_butt_name = the_butt._name
        # print(the_butt_name)
        for line_i in range(len(self.lines)):
            # print(n._name)
            if (self.idlist[line_i * 4]._name == the_butt_name):
                new_id = self.idlist[line_i * 4 + 3].get()
                try:
                    new_idn = int(new_id)
                except ValueError:
                    # tkinter.messagebox.showinfo(title='错误', message='必须是0到2的数字')
                    self.outlog.set('Error：0到2的数字')
                    break
                if (new_idn not in range(0, 3)):
                    # tkinter.messagebox.showinfo(title='错误', message='必须是0到2的数字')
                    # self.text_outlog.delete(0, 100)
                    self.outlog.set('Error：0到2的数字')
                    break
                # print(new_id)
                # print(self.lines[line_i])
                newlines = []
                for i in range(len(self.lines)):
                    if (i == line_i):
                        newlines.append(str(new_idn) + self.lines[i][1:])
                    else:
                        newlines.append(self.lines[i])

                with open(self.labels[self.labelcnt]['annpath'], 'w') as annfile:
                    annfile.writelines(newlines)
                self.outlog.set('修改成功！第' + str(line_i + 1) + "行")
                break
        ims = Image.open(self.labels[self.labelcnt]['framepath'])
        ims = ims.resize((1703, 958))
        self.draw_bbox(ims)
        self.image = ImageTk.PhotoImage(ims)
        self.canvas.create_image(0, 0, anchor='nw', image=self.image)
        self.root.title(self.labels[self.labelcnt]['framepath'])

    def but_deleteCaptureClick(self, event):
        # 删除标注文件中对应行
        # top = tkinter.Toplevel()
        # top.title('警告')
        # msg = tkinter.Message(top,text='删除不可复原，确认删除？',width=150)
        # msg.pack()
        a = tkinter.messagebox.askokcancel('警告', '删除不可复原，确认删除？')

        if (a is False):
            return
        else:
            the_butt = event.widget
            the_butt_name = the_butt._name
            for line_i in range(len(self.lines)):
                # print(n._name)
                if (self.idlist[line_i * 4 + 1]._name == the_butt_name):
                    newlines = []
                    for i in range(len(self.lines)):
                        if (i == line_i):
                            continue
                        else:
                            newlines.append(self.lines[i])

                    with open(self.labels[self.labelcnt]['annpath'], 'w') as annfile:
                        annfile.writelines(newlines)
                    self.outlog.set('删除成功！第' + str(line_i + 1) + "行")
                    break
            ims = Image.open(self.labels[self.labelcnt]['framepath'])
            ims = ims.resize((1703, 958))
            self.draw_bbox(ims)
            self.image = ImageTk.PhotoImage(ims)
            self.canvas.create_image(0, 0, anchor='nw', image=self.image)
            self.root.title(self.labels[self.labelcnt]['framepath'])

    def but_addCaptureClick(self):
        # 新添加Label控件和Entry控件以及Button，接收在canvas中点出的框坐标
        self.canvas.create_rectangle(self.selectPosition[0], self.selectPosition[2], self.selectPosition[1],
                                     self.selectPosition[3], outline="red")
        w = self.selectPosition[1] - self.selectPosition[0]
        h = self.selectPosition[3] - self.selectPosition[2]
        x = (self.selectPosition[0] + w / 2) / 1703.0
        y = (self.selectPosition[2] + h / 2) / 958.0
        w = w / 1703.0
        h = h / 958.0
        bbox = ('0', str('%.6f' % x), str('%.6f' % y), str('%.6f' % w), str('%.6f' % h))
        new_line = ' '.join(bbox)
        print(new_line)
        self.lines.append(new_line)
        with open(self.labels[self.labelcnt]['annpath'], 'w') as annfile:
            annfile.writelines(self.lines)
        self.outlog.set('添加成功！请标注\n第' + str(self.num + 1) + '行')
        ims = Image.open(self.labels[self.labelcnt]['framepath'])
        ims = ims.resize((1703, 958))
        self.draw_bbox(ims)
        self.image = ImageTk.PhotoImage(ims)
        self.canvas.create_image(0, 0, anchor='nw', image=self.image)
        self.root.title(self.labels[self.labelcnt]['framepath'])

    def destroy_idbar(self):
        for e in self.idlist:
            e.destroy()
        self.idlist = []
        # self.text_outlog.delete(0, 100)

    def draw_bbox(self, im):
        self.destroy_idbar()
        draw = ImageDraw.Draw(im)
        self.lines = []
        try:
            with open(self.labels[self.labelcnt]['annpath'], 'r') as f:
                self.lines = f.readlines()
        except FileNotFoundError:
            right = self.labels[self.labelcnt]['annpath'].rfind('/')
            folder = self.labels[self.labelcnt]['annpath'][:right]
            #print(self.labels[self.labelcnt]['annpath'])
            if not os.path.exists(folder):
                #print(folder)
                #print(self.labels[self.labelcnt]['annpath'])
                os.mkdir(folder)
            with open(self.labels[self.labelcnt]['annpath'], 'w') as f:
                pass
        if (len(self.lines) > 0 and self.lines[-1] == '\n'):
            self.lines.pop()

        bboxs = []
        ids = []
        for i in range(len(self.lines)):
            if ('\n' not in self.lines[i]):
                self.lines[i] = self.lines[i] + '\n'
            line = self.lines[i].strip().split(' ')
            bboxs.append([line[1], line[2], line[3], line[4]])
            ids.append([line[0]])
        print(self.lines, len(self.lines))
        self.num = 0
        for b, i in zip(bboxs, ids):
            # print(type(b),b[0],b[1])
            self.num += 1
            xmin = int((float(b[0]) - float(b[2]) / 2.) * 1703)
            ymin = int((float(b[1]) - float(b[3]) / 2.) * 958)
            xmax = int((float(b[0]) + float(b[2]) / 2.) * 1703)
            ymax = int((float(b[1]) + float(b[3]) / 2.) * 958)
            draw.rectangle((xmin, ymin, xmax, ymax), outline=(0, 255, 15))
            idt = self.idtext[i[0]]
            font1 = ImageFont.truetype("C:/Windows/Fonts/simsunb.ttf", 24)
            draw.ink = 0 + 0 * 256 + 0 * 256 * 256
            draw.rectangle((xmin, ymin - 30, xmin + 120, ymin), fill=128)
            draw.text((xmin, ymin - 30), str(self.num) + ' ' + idt, font=font1)
            text = tkinter.Label(self.root, text=str(self.num))
            text.place(x=1710, y=50 + 35 * (self.num - 1), width=20, height=30)
            e = tkinter.Entry(self.root)
            e.insert(0, i[0])
            e.place(x=1731, y=50 + 35 * (self.num - 1), width=30, height=30)
            but_confirm = tkinter.Button(self.root, text="确认")
            but_confirm.place(x=1780, y=50 + 35 * (self.num - 1), width=50, height=30)
            but_confirm.bind('<Button-1>', self.but_confirmCaptureClick)
            # but_confirm.bind('<ButtonRelease-1>',self.but_confirmrelease)
            but_delete = tkinter.Button(self.root, text="删除")
            but_delete.place(x=1831, y=50 + 35 * (self.num - 1), width=50, height=30)
            but_delete.bind('<Button-1>', self.but_deleteCaptureClick)

            self.idlist.append(but_confirm)
            self.idlist.append(but_delete)
            self.idlist.append(text)
            self.idlist.append(e)
            # but_add = tkinter.Button(self.root, text="添加", command=self.but_addCaptureClick)
            # but_add.place(x=1780, y=50 + 35 * (self.num), width=50, height=30)
            # self.idlist.append(but_add)

DEVICE = ['设备1']
ZKDATE = {'_1EF40468_1531197520':'2018.7.3',
          '_1E7ABC08_1531197647':'2018.7.4',
          '_1EF585F0_1531203342':'2018.7.5',
          '_1E9D6B10_1531210045':'2018.7.6',
          '_17BA01E0_1531210125':'2018.7.7'}
def mvtxt(analys_out):
    cnt = 0
    c = 0
    cc = 0

    for t in os.listdir(analys_out):
        if os.path.isfile(analys_out + t):
            cnt += 1
            if not os.path.exists(analys_out + t[:t.rfind('_')]):
                os.mkdir(analys_out + t[:t.rfind('_')])
            if t[t.rfind('_'):][1] == 'b':
                c += 1
                os.rename(analys_out + t, analys_out + t[:t.rfind('_')] + '/' + t)
            else:
                cc += 1
                os.rename(analys_out + t, analys_out + t[:t.rfind('.')] + '/' + t)


def ch_time(analys_out):
    for tn in os.listdir(analys_out):
        if os.path.isdir(analys_out + tn):
            lines = []
            with open(analys_out + tn + '/' + tn + '.txt', 'r') as f:
                lines = f.readlines()

            newlines = []
            for line in lines:
                t = line.strip().split(' ')
                s = int(t[0]) / 25

                line = str(s)
                s = int(t[1]) / 25

                line = line + ' ' + str(s) + '\n'
                newlines.append(line)

            with open(analys_out + tn + '/' + tn + '_changetime.txt', 'w') as f:
                f.writelines(newlines)


def cut(videodir, analys_out):
    # videodir是原视频所在路径，analys_out是分析结果把时间从帧数换算为秒数的文本文件路径
    cnt = 0
    flag = 0

    for vn in os.listdir(videodir):
        name = vn[:vn.rfind('.')]       # 找出mp4文件的名字
        for ds in os.listdir(analys_out + name + '/'):
            if ds[:ds.rfind('_')] == 'cuted':       # 对应名字的文件夹下如果有已经切过的
                flag = 1
                break

        if flag == 1:                                  # 就跳过
            cnt += 1
            flag = 0
            continue

        clip = VideoFileClip(videodir + vn)             # clip是剪辑类对象
        lines = []
        with open(analys_out + name + '/' + name + '_changetime.txt', 'r') as f:
            lines = f.readlines()

        i = 0
        for line in lines:
            i += 1
            line = line.strip().split(' ')
            s = int(line[0])
            e = int(line[1])
            c = clip.subclip(s, e)                      # clip剪辑从s到e的视频段
            c.to_videofile(analys_out + name + "/cuted_" + str(i) + ".mp4", fps=25, remove_temp=False)
                                                        # 保存
        clip.reader.close()
        cnt += 1


# 给剪辑视频添加标注 将地址和属性写进数据库
def init_db(db_host, db_name, db_username, db_pwd, db_charset):
    pass
    try:
        conn = pymssql.connect(db_host,db_name,db_username,db_pwd)
    except Exception as err:
        print("Error decoding config file: %s" % str(err))
        sys.exit(1)
    return conn

def close_db(conn):
    try:
        conn.close()
    except Exception as err:
        print("Error decoding config file: %s" % str(err))
        sys.exit(1)

def write_db(conn,filename,path,date,duration,device,category):
    cur = conn.cursor()
    cat = 0
    if 1 in category:
        cat |= 0b01
    if 2 in category:
        cat |= 0b10

    try:
        cur.execute("insert into chaxun1(filename,path,date,duration,device,category) VALUES ('%s','%s','%s',%d,'%s',%d)" % (filename,path,date,duration,device,cat))
        conn.comit()
        cur.close()
    except Exception as err:
        print("Error decoding config file: %s" % str(err))
        sys.exit(1)

def name(analys_out, conn):
    cnt = 0
    count = 0
    changename = ''
    last = 1
    end = 0
    flag = 1
    sflag = 0
    eflag = 0
    rflag = 0
    dflag = 0
    flagphone = 0
    flagsleep = 0
    yichang = 0
    names = ['norm', 'lookphone ', 'sleep ']
    start = []
    stop = []
    cfn = 0
    tui = 0
    filename = ''
    path = ''
    date = ''
    duration = []
    device = ''
    category = set()


    for d in os.listdir(analys_out):
        duration = []
        if os.path.isdir(analys_out + d):
            tlines = []
            with open(analys_out + d + '/' + d + '.txt', 'r') as f1:  # 读取帧数起止文件
                tlines = f1.readlines()

            lines = []
            with open(analys_out + d + '/' + d + '_bbox.txt', 'r') as f:  # 读取每帧bbox文件
                lines = f.readlines()

            for tl in tlines:
                if tl[0] == '\n':
                    break
                start.append(tl.strip().split(' ')[0])
                stop.append(tl.strip().split(' ')[1])
                duration.append(int(tl.strip().split(' ')[1]) - int(tl.strip().split(' ')[0]))
                cnt += 1
            print(cnt)
            # if cnt == 12 :
            #     pass
            cc = cnt
            for i in range(0, cc):
                category.clear()
                path = ''
                filename = ''
                device = ''
                date = ''
                for line in lines:
                    if line.find('frame') == 0:         # 这一行是帧数行
                        if last - 1 == cnt:             # last-1 == cnt表示所有一场片段处理完了
                            if dflag:
                                videowriter.write(frame)
                            videowriter.release()
                            cap.release()
                            write_db(conn, filename, path, date, math.ceil(duration[last-2]/25.0), device, category)
                            dflag = 0
                            tui = 0
                            last = 1
                            start = []
                            stop = []
                            cnt = 0
                            break

                        line = line.strip().split(':')
                        if line[1] == start[last - 1]:
                            sflag = 1
                        if line[1] == stop[last - 1]:
                            eflag = 1
                        if sflag:
                            rflag = 1
                        if dflag:
                            # cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_CUBIC)
                            # param = []
                            # param.append(1)
                            # cv2.imwrite("d:/phone/test/ss_" + str(cfn) + ".jpg", frame, param)
                            videowriter.write(frame)
                            dflag = 0
                            if sflag == 0:
                                videowriter.release()
                                cap.release()
                                write_db(conn, filename, path, date, math.ceil(duration[last - 2] / 25.0), device,
                                         category)
                                tui = 0
                                rflag = 0
                                break
                            else:
                                pass
                        elif tui:
                            videowriter.release()
                            cap.release()
                            write_db(conn, filename, path, date, math.ceil(duration[last-2]/25.0), device, category)
                            tui = 0
                            rflag = 0
                            break
                        if (flag):
                            print(d, last)
                            cap = cv2.VideoCapture(analys_out + d + '/' + 'cuted_' + str(last) + '.mp4')
                            fps = 25
                            size = (1920, 1080)
                            filename = 'bbox_result_' + str(last) + '.mp4'
                            # 以后开发根据原视频名判断属于哪个DEVICE的功能
                            # 以后开发根据原视频名判断日期
                            device = DEVICE[0]
                            date = ZKDATE[d[d.find('_'):]]
                            path = analys_out + d + '/' + filename
                            videowriter = cv2.VideoWriter(path, cv2.VideoWriter_fourcc('D', 'I', 'V', 'X'), fps, size)
                            flag = 0
                        if eflag:
                            tui = 1
                            sflag = 0
                            eflag = 0
                            last += 1
                            flag = 1
                    else:
                        if rflag:
                            success, frame = cap.read()
                            cfn += 1
                            # print(type(frame))
                            # cv2.imshow('sfd', frame)
                            # cv2.waitKey(10000)
                            rflag = 0
                            dflag = 1

                        line = line.strip().split(' ')
                        cls = int(line[0])
                        category.add(cls)
                        x = float(line[1]) * 1920
                        y = float(line[2]) * 1080
                        w = float(line[3]) * 1920
                        h = float(line[4]) * 1080
                        x1 = int(x - 0.5 * w)
                        y1 = int(y - 0.5 * h)
                        x2 = int(x + 0.5 * w)
                        y2 = int(y + 0.5 * h)
                        if dflag:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            cv2.rectangle(frame, (x1, y1 - 30), (x1 + 150, y1), (255, 0, 0), -1)
                            cv2.putText(frame, names[cls], (x1, y1 - 10), cv2.FONT_HERSHEY_COMPLEX, 0.75, (0, 0, 0), 2)
                            # cv2.imshow("sdf",frame)
                            # cv2.waitKey(0)

        # break



def findbadvideo(videodir, outdir, ffprobe_path):
    sum = 0
    for d in os.listdir(videodir):
        if ('7号' in d):
            for each_video in os.listdir(videodir + d):
                if ('mp4' in each_video):
                    filename = videodir + d + '/' + each_video
                    # filename = "d:/phone/python/7号高炉中控室_1E7ABC08_1531197647_52.mp4"
                    result = subprocess.Popen([ffprobe_path, filename],
                                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    for x in result.stdout.readlines():
                        x = str(x, 'utf-8')
                        if ("Duration" in x):
                            # print(type(x),x,x[4])
                            t = x.split(',')
                            m = t[0].split(':')[1:][1]
                            s = t[0].split(':')[1:][2].split('.')[0]
                            if (int(m) * 60 + int(s) > 1095):
                                sum += 1
                                shutil.copyfile(filename, outdir + filename.split('/')[3])


def repairvideo(badvideodir, outdir, liwai):
    fps = 25
    for each_video in os.listdir(badvideodir):
        name = each_video[each_video.find('_'):each_video.rfind('.')]
        if name == liwai:
            print("生成视频中 : " + outdir + each_video)
            fourcc = cv2.VideoWriter_fourcc('D', 'I', 'V', 'X')
            video_writer = cv2.VideoWriter(filename=outdir + name + '.mp4', fourcc=fourcc, fps=fps,
                                           frameSize=(1280, 720))
            im_names = os.listdir(outdir + name)
            for im_name in range(len(im_names)):
                if os.path.exists(outdir + name + '/' + name + '_' + str(im_name) + '.jpg'):
                    img = cv2.imread(filename=outdir + name + '/' + name + '_' + str(im_name) + '.jpg')
                    # print(im_name)
                    img = cv2.resize(img, (1280, 720), interpolation=cv2.INTER_CUBIC)
                    video_writer.write(img)

            print(outdir + name + '/' + name + '_' + str(im_name) + '.jpg' + ' done!')
            video_writer.release()
            cv2.waitKey(10)
            try:
                os.system("rd/s/q " + outdir + name)
            except Exception as e:
                pass
                print(e)
            continue

        vc = cv2.VideoCapture(badvideodir + each_video)
        print(badvideodir + each_video)
        c = 1
        if vc.isOpened():
            rval, frame = vc.read()
        else:
            rval = False
        while rval:
            # print('1')
            rval, frame = vc.read()
            # cv2.imshow("sdf",frame)
            # rows, cols, channel = frame.shape
            # if((c) == 0):
            # print(outdir + name+'/'+name + '_'+str(int(c)) + '.jpg')
            cv2.imwrite(outdir + name + '/' + name + '_' + str(int(c)) + '.jpg', frame)
            c = c + 1
            # cv2.waitKey(1)
        vc.release()

        fourcc = cv2.VideoWriter_fourcc('D', 'I', 'V', 'X')
        video_writer = cv2.VideoWriter(filename=outdir + name + '.mp4', fourcc=fourcc, fps=fps,
                                       frameSize=(1280, 720))
        im_names = os.listdir(outdir + name)
        for im_name in range(len(im_names)):
            if os.path.exists(outdir + name + '/' + name + '_' + str(im_name) + '.jpg'):
                img = cv2.imread(filename=outdir + name + '/' + name + '_' + str(im_name) + '.jpg')
                # print(im_name)
                img = cv2.resize(img, (1280, 720), interpolation=cv2.INTER_CUBIC)
                video_writer.write(img)
                print(outdir + name + '/' + name + '_' + str(im_name) + '.jpg' + ' done!')

        video_writer.release()
        cv2.waitKey(10)
        try:
            os.system("rd/s/q " + outdir + name)
        except Exception as e:
            pass
            print(e)


def cap_video(videodir, outdir, exepath, cap_name):
    videoname = []
    for file in os.listdir(videodir):
        if cap_name in file:
            for mp4 in os.listdir(videodir + file):
                index = mp4.rfind('.')
                videoname.append([mp4[:index], file])

    cnt = 0
    for name, file in videoname:
        try:
            os.makedirs(outdir + name)
        except FileExistsError:
            print("已存在：" + outdir + name)
            continue
        except Exception as e:
            print(e)
            exit(0)
        cmd = "start /min " + exepath + " " + outdir + name + " cap_video " + videodir + file + "/" + name + ".mp4 600"
        print(cmd)
        cnt += 1

        if cnt < 20:
            os.system(cmd)
        else:
            cmd = "start /min /wait " + exepath + " " + outdir + name + " cap_video " + videodir + file + "/" + name + ".mp4 600"
            print(cmd)
            os.system(cmd)
            cnt = 0
            time.sleep(60)


def change_key(framesdir, chkey):
    if chkey == '7号高炉中控室':
        key = '7'
    elif chkey == '大棒线粗轧轧机区':
        key = 'da'
    for d in os.listdir(framesdir):
        newname = d.replace(chkey, key)
        os.rename(framesdir + d, framesdir + newname)
        for f in os.listdir(framesdir + newname):
            n = f.replace(chkey, key)
            os.rename(framesdir + newname + '/' + f, framesdir + newname + '/' + n)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-cls', default='cut', help='cls of interface')
    parser.add_argument('-analys_out', default='', help='path to analys_out\n')
    parser.add_argument('-videodir', default='\\path\\to\\videodir',
                        help='path to videodir\n')
    parser.add_argument('-repair_out', default='\\path\\to\\repairoutdir',
                        help='path to after repair dir')
    parser.add_argument('-repair_except', default='', help='except not to repair')
    parser.add_argument('-cap_out', default='', help='cap_video frame out dir')
    parser.add_argument('-cap_exe', default='', help='cap_frames tool exe path')
    parser.add_argument('-cap_name', default='', help='first name of mp4')
    parser.add_argument('-framesdir', default='', help='path to frames dir\n')
    parser.add_argument('-annsdir', default='', type=str,
                        help='Output annotations directory\n')
    parser.add_argument('-mark_cls', default='', help='mark cls: zhongkong zhaxian\n')
    parser.add_argument('-key', default='', help='key of mp4 name\n')
    parser.add_argument('-drop', default='', help='drop out dir\n')
    parser.add_argument('-db_username', default='', help='username\n')
    parser.add_argument('-db_pwd', default='', help='pwd\n')
    parser.add_argument('-db_host', default='', help='db host\n')
    parser.add_argument('-db_name', default='', help='db name\n')
    parser.add_argument('-db_charset', default='', help='db charset\n')
    parser.add_argument('-ffprobe_path', default='', help='path to ffprobe\n')

    args = parser.parse_args()
    # 剪辑视频
    if (args.cls == "cut"):
        mvtxt(args.analys_out)
        ch_time(args.analys_out)
        cut(args.videodir, args.analys_out)
        conn = init_db(args.db_host, args.db_name, args.db_username, args.db_pwd, args.db_charset)
        name(args.analys_out, conn)
        close_db(conn)
    elif (args.cls == "repair"):  # 修复视频
        findbadvideo(args.videodir, args.repair_out, args.ffprobe_path)
        repairvideo(args.repair_out, args.videodir)
    elif (args.cls == "cap_video"):  # 获取视频帧
        cap_video(args.videodir, args.cap_out, args.cap_exe, args.cap_name)
    elif (args.cls == "mark"):  # 标注工具
        w = MyGui(args.framesdir, args.annsdir, args.mark_cls,args.drop)
    elif (args.cls == "chkey"):  # 替换掉文件名中的中文
        change_key(args.framesdir, args.key)


if __name__ == '__main__':
    main(sys.argv)

