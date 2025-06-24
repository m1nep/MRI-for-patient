import tkinter as tk
from tkinter import *
from tkinter import ttk
import nibabel as nib
import numpy as np
from PIL import Image, ImageTk
import shutil
import os
import sqlite3
# Путь к изображению, маске, файлу с заметками
mri_name='t2'
image_path = f'images\\{mri_name}.nii.gz'  # Укажите путь к вашему изображению
backup_path = 'images\\{mri_name}_backup.nii.gz'# Путь для копии файла
db_path='images\\{mri_name}_db.db' #Путь db
mask_mri_name="t2_anatomy_reader1"
mask_image_path = f'images\\{mask_mri_name}.nii.gz'  # Укажите путь к вашему изображению
mask_backup_path = 'images\\{mask_mri_name}_backup.nii.gz'# Путь для копии файла
mask_db_path='images\\{mask_mri_name}_db.db' #Путь db

# Копирование исходного файла (если копия ещё не существует)
def create_backup():
    if not os.path.exists(backup_path):  # Проверяем, если копия файла не существует
        shutil.copy(image_path, backup_path)  # Копируем файл в новое место

# Переключение на показ маски по умолчанию
mask_flag=True

# Загружаем изображение
def load_image(image_path1):
    image_obj = nib.load(image_path1)  # Открываем оригинальный файл
    return image_obj.get_fdata()

# Создание копии файла (не используется, но лучше с ним)
create_backup()

# Нормализация изображения (если нужно)
def normalize_image(img_data):
    # Нормализуем изображение, чтобы значения пикселей находились в диапазоне [0, 255]
    min_val = np.min(img_data)
    max_val = np.max(img_data)
    norm_img = ((img_data - min_val) / (max_val - min_val) * 255).astype(np.uint8)
    return norm_img

# Текущий слой по умолчанию
current_layer = 0

# Инициализация окна
root = tk.Tk()
w = root.winfo_screenwidth()
h = root.winfo_screenheight()
root.title("Просмотр МРТ")
root.geometry(f"{w}x{h}")

# Загружаем данные изображения
image_data = load_image(image_path)
mask_data=load_image(mask_image_path)
k_h=h/image_data.shape[0]-1

# Масштабирование изображения под размер окна
image_data=np.repeat(np.repeat(image_data,k_h,axis=1),k_h,axis=0)
mask_data=np.repeat(np.repeat(mask_data,k_h,axis=1),k_h, axis=0)
height, width, depth = image_data.shape
maxval = depth - 1

# Создание фрейма для рисования
frame = ttk.Frame(root)
frame.grid(row=0, column=1, rowspan=5, padx=10, pady=10)

# Canvas для отображения изображения
canvas = tk.Canvas(frame, width=width, height=height)
canvas.grid(row=0, column=1, rowspan=5, padx=5, pady=5)

# Ползунок для выбора слоя
slider = ttk.Scale(root, from_=0, to=maxval, orient="horizontal", command=lambda val: update_image(int(float(val))))
slider.grid(row=6, column=1, padx=10, pady=10)

# Флаг для предотвращения рекурсии
updating_slider = False

# Перевод изображения из 3d (где 1 измерение - номер слоя), в 4d (где добавляются измерения для цвета)
newd_data=np.zeros((image_data.shape[0], image_data.shape[1], image_data.shape[2], 3))  
for x in range(image_data.shape[0]):
    for y in range(image_data.shape[1]):
        for z in range(image_data.shape[2]):
            newd_data[x,y,z,0]=newd_data[x,y,z,1]=newd_data[x,y,z,2]=image_data[x,y,z]
image_data=newd_data

new_mask_data=np.zeros((mask_data.shape[0], mask_data.shape[1], mask_data.shape[2], 3))  
for x in range(image_data.shape[0]):
    for y in range(image_data.shape[1]):
        for z in range(image_data.shape[2]):
            new_mask_data[x,y,z,0]=mask_data[x,y,z]
mask_data=new_mask_data
new_data=image_data
for x in range(image_data.shape[0]):
    for y in range(image_data.shape[1]):
        for z in range(image_data.shape[2]):
            if mask_data[x,y,z,0]==1:
                
                new_data[x,y,z,1]=new_data[x,y,z,1]-200
                new_data[x,y,z,2]=new_data[x,y,z,2]-200
            elif mask_data[x,y,z,0]==2:
                new_data[x,y,z,0]=new_data[x,y,z,0]-200
                new_data[x,y,z,2]=new_data[x,y,z,2]-200
            
new_data=normalize_image(new_data)

# Функция для отображения слоя
def update_image(layer):
    global current_layer, updating_slider, mask_flag
    if mask_flag==True:
        img_array=new_data[:,:,layer,:]
        
    else:
        img_array=image_data[:,:,layer,:]
    text_del()

    if updating_slider:  
        return

    current_layer = layer
 
    canvas.delete("all")

    norm_img = normalize_image(img_array)
    
    # Используем PIL для преобразования массива в изображение
    img_pil = Image.fromarray(norm_img)
    img_tk = ImageTk.PhotoImage(img_pil)

    # Отображаем изображение на Canvas
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
    canvas.image = img_tk  # Сохраняем ссылку на изображение, чтобы оно не исчезло

    # Обновляем ползунок
    updating_slider = True
    slider.set(current_layer)
    updating_slider = False
    update_layers(current_layer) 
    insert_cur_text()
# Рисование линий по умолчанию
draw_tool = "pen"  # Текущий инструмент
color = "red"  # Текущий цвет

# Для рисования
start_x = start_y = None  # Начальные координаты
is_drawing = False  # Флаг, определяющий состояние рисования

# Функция для начала рисования
def start_drawing(event):
    global start_x, start_y, drawing_figure, is_drawing
    start_x, start_y = event.x, event.y
    is_drawing = True 
    drawing_figure = None
global pic
pic=np.zeros((height,width,3,depth), dtype="uint8")

# Функция для рисования
def draw(event):
    global start_x, start_y, drawing_figure, is_drawing

    if not is_drawing:
        return  

    if start_x is None or start_y is None:
        return
    if color=="red":
        col=0,
    elif color=="green":
        col=1
    elif color=="blue":
        col=2
    # Рисование с учетом координат
    if draw_tool == "pen":
        canvas.create_line(start_x, start_y, event.x, event.y, fill=color, width=2)
        pic[start_x,start_y,col,current_layer]=255
        start_x, start_y = event.x, event.y
        pic[event.x, event.y, col, current_layer]=255
        
# Функция для выбора инструмента
def select_tool(tool):
    global draw_tool
    draw_tool = tool

# Функция для выбора цвета
def select_color(selected_color):
    global color
    color = selected_color

# Кнопки для выбора цвета
button_red = ttk.Button(root, text="Красный", command=lambda: select_color("red"))
button_red.grid(row=1, column=2, padx=5, pady=5)

button_blue = ttk.Button(root, text="Синий", command=lambda: select_color("blue"))
button_blue.grid(row=2, column=2, padx=5, pady=5)

button_green = ttk.Button(root, text="Зелёный", command=lambda: select_color("green"))
button_green.grid(row=3, column=2, padx=5, pady=5)

# Добавление кнопки для рисования
button_pen = ttk.Button(root, text="Рисовать", command=lambda: select_tool("pen"))
button_pen.grid(row=0, column=2, padx=5, pady=5)

# Функция для сохранения рисунка текущего слоя
def save_current_layer():
    save_to_file()

# Кнопка для сохранения рисунка
save_button = ttk.Button(root, text="Сохранить рисунок", command=save_current_layer)
save_button.grid(row=7, column=1, columnspan=4, padx=5, pady=5)

# Кнопка для изменения состояния показа маски (не работает??)
def reverse_mask():
    global mask_flag
    if mask_flag==True:
        mask_flag=False
    else:
        mask_flag=True
    update_image(current_layer)
    update_layers(current_layer) 
        
# Кнопка для включения маски
reverse_button=ttk.Button(root, text="Включить маску", command=reverse_mask)
reverse_button.grid(row=8, column=1, columnspan=4, padx=5, pady=5)

# Функция для сохранения отдельного слоя с рисунками в файл.png
def save_to_file():
    if mask_flag:
        image_saving=normalize_image(new_data[:,:,current_layer,:])
    else:
        image_saving=normalize_image(image_data[:,:,current_layer,:])
    for color in 0,1,2: 
        for save_h in range(height):
            for save_w in range(width):
                if pic[save_h,save_w,color,current_layer]!=0:
                    image_saving[save_h,save_w,color]=pic[save_h,save_w,color,current_layer]
    im=Image.fromarray(image_saving[:,:,:])
    im.save(f'{mri_name}_{current_layer}.png')

# Добавление метки для слоя
label_layers = ttk.Label(root, text="Слой: 0")
label_layers.grid(row=6, column=2, padx=10, pady=10)

# Добавление поля с текстом
entry_text=ttk.Entry(root)
entry_text.grid(row=7, column=2, padx=10,pady=10)

# Вводим текст из db
def insert_cur_text():
    connection=sqlite3.connect(f'images\\{mri_name}_db.db')
    cursor=connection.cursor()
    cursor.execute(f'''SELECT layer_text FROM {mri_name} WHERE layer_name = ({current_layer})
                       
        ''')
    current_text=cursor.fetchone()
    connection.commit()
    connection.close()
    if current_text==(None,):
        current_text=""
    
    entry_text.insert(0,current_text)
insert_cur_text()

# Удаляем текст заметки при изменении слоя
def text_del():
    entry_text.delete(0, END)

def save_text():
    text=text_get()
    connection=sqlite3.connect(f'images\\{mri_name}_db.db')
    cursor=connection.cursor()
    cursor.execute(f'''UPDATE {mri_name} SET layer_text = ({f'{text}'}) WHERE layer_name = ({current_layer})
                       
        ''')
    connection.commit()
    connection.close()

# Кнопка для сохранения заметок
save_button_text = ttk.Button(root, text="Сохранить заметку", command=save_text)
save_button_text.grid(row=8, column=2, columnspan=4, padx=5, pady=5)

def text_get():
    text=entry_text.get()
    return text

# Функция для обновления обновления слоёв
def update_layers(layer):
    current_layer=layer
    label_layers.config(text=f"Cлой: {current_layer}")  # Обновление текста

# Функция для обновления координат
def update_coords(event):
    x, y = event.x, event.y

    update_layers(current_layer) 

# Привязка событий для рисования и отслеживания координат
canvas.bind('<ButtonPress-1>', start_drawing)  # Начало рисования
canvas.bind('<B1-Motion>', draw)  # Процесс рисования
canvas.bind('<Motion>', update_coords)  # Обновление координат

# Функция для работы с клавишами для перемещения слоев
def on_key_press(event):
    if event.keysym == "Right":
        move_layer("next")
    elif event.keysym == "Left":
        move_layer("prev")

# Привязка стрелок для перемещения между слоями
root.bind("<Left>", on_key_press)
root.bind("<Right>", on_key_press)

# Функция для перемещения между слоями
def move_layer(direction):
    global current_layer
    if direction == "next" and current_layer < maxval:
        current_layer += 1
    elif direction == "prev" and current_layer > 0:
        current_layer -= 1
    update_image(current_layer)
    update_layers(current_layer) 
    text_del()
    insert_cur_text()
       
# Инициализация отображения первого слоя
update_image(0)

# Завершение работы после закрытия окна
def on_close():
    root.quit()

root.protocol("WM_DELETE_WINDOW", on_close)

# Запуск приложения
root.mainloop()
