# Для считывания PDF
import PyPDF2
# Для анализа структуры PDF и извлечения текста
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure, LTPage, LTImage, LTContainer
from pdfminer.image import ImageWriter
# Для извлечения текста из таблиц в PDF
import pdfplumber
# Для извлечения изображений из PDF
from PIL import Image
from pdf2image import convert_from_path
# Для выполнения OCR, чтобы извлекать тексты из изображений
# import pytesseract
# Для удаления дополнительно созданных файлов
import os
import pandas as pd
from translate import Translator

def get_image(layout_object):
    if isinstance(layout_object, LTImage):
        return layout_object
    if isinstance(layout_object, LTContainer): # LTContainer
        for child in layout_object:
            if isinstance(child, LTImage):
                return (child)
            # return get_image(child)
    else:
        return None
def save_images_from_page(page: LTPage, pagenum):
    images = list(filter(bool, map(get_image, page)))
    # print(images)
    iw = ImageWriter('cropped/' +pagenum)
    # print(images)
    for image in images:
        # print(os.path.exists('./cropped/img5.jpg'))
        if (not os.path.exists('./cropped/' + pagenum +'/' + image.name + '.jpg')) & \
            (not os.path.exists('./cropped/' + pagenum +'/' + image.name + '.bmp')):
            # print(image.name)
            # os.mkdir('./cropped/'+ pagenum)
            iw.export_image(image)
            if os.path.exists('./cropped/' + pagenum + '/' + image.name + '.jpg'):
                nwimage = Image.open('./cropped/' + pagenum +'/' + image.name + '.jpg').convert("RGBA")
                new_image = Image.new("RGBA", nwimage.size, "WHITE")  # Create a white rgba background
                new_image.paste(nwimage, (0, 0), mask=nwimage)  # Paste the image on the background. Go to the links given below for details.
                datas = new_image.getdata()
                #Меняем черный на белый
                new_image_data = []
                for item in datas:
                    # change all white (also shades of whites) pixels to yellow
                    if item[0] in list(range(0, 25)):
                        new_image_data.append((255, 255, 255))
                    else:
                        new_image_data.append(item)

                # update image data
                new_image.putdata(new_image_data)
                new_image.convert('RGB').save('./cropped/' + pagenum +'/' + image.name + '_.jpg', "JPEG")
            # iw.show('image')
            # if (os.path.exists('./cropped/' + image.name + '.jpg')):
            #     im = Image.open('./cropped/' + image.name+ '.jpg')
            #     im.show()
            #      filename = input('Как назвать?')

# Создаём функцию для извлечения текста
def text_extraction(element):
    # Извлекаем текст из вложенного текстового элемента
    line_text = element.get_text()

    # Находим форматы текста
    # Инициализируем список со всеми форматами, встречающимися в строке текста
    line_formats = []
    for text_line in element:
        if isinstance(text_line, LTTextContainer):
            # Итеративно обходим каждый символ в строке текста
            for character in text_line:
                if isinstance(character, LTChar):
                    # Добавляем к символу название шрифта
                    line_formats.append(character.fontname)
                    # Добавляем к символу размер шрифта
                    line_formats.append(character.size)
    # Находим уникальные размеры и названия шрифтов в строке
    format_per_line = list(set(line_formats))

    # Возвращаем кортеж с текстом в каждой строке вместе с его форматом
    return (line_text, format_per_line)


# Извлечение таблиц из страницы

def extract_table(pdf_path, page_num, table_num):
    # Открываем файл pdf
    pdf = pdfplumber.open(pdf_path)
    # Находим исследуемую страницу
    table_page = pdf.pages[page_num]
    # Извлекаем соответствующую таблицу
    table = table_page.extract_tables()[table_num]
    return table

# Преобразуем таблицу в соответствующий формат
def table_converter(table):
    table_string = ''
    translator = Translator(from_lang='zh-cn', to_lang='ru')
    # Итеративно обходим каждую строку в таблице
    df = pd.DataFrame()
    for row_num in range(len(table)):
        row = table[row_num]
        # Удаляем разрыв строки из текста с переносом
        cleaned_row = [item.replace('\n', ' ') if item is not None and '\n' in item else 'None' if item is None else item for item in row]
        if len(cleaned_row) > 0:
            # print(cleaned_row)
            rusrow = [translator.translate(item) for item in cleaned_row]
            df_ = pd.DataFrame([('|'+'|'.join(rusrow)+'|'+'\n').split('|')])
            df = pd.concat([df, df_])
        # Преобразуем таблицу в строку
        table_string+=('|'+'|'.join(cleaned_row)+'|'+'\n')
    # Удаляем последний разрыв строки
    table_string = table_string[:-1]

    return table_string, df

# Создаём функцию для вырезания элементов изображений из PDF
def crop_image(element, pageObj):
    # Получаем координаты для вырезания изображения из PDF
    [image_left, image_top, image_right, image_bottom] = [element.x0,element.y0,element.x1,element.y1]
    # Обрезаем страницу по координатам (left, bottom, right, top)
    pageObj.mediabox.lower_left = (image_left, image_bottom)
    pageObj.mediabox.upper_right = (image_right, image_top)
    # Сохраняем обрезанную страницу в новый PDF
    cropped_pdf_writer = PyPDF2.PdfWriter()
    cropped_pdf_writer.add_page(pageObj)
    # Сохраняем обрезанный PDF в новый файл
    with open('cropped_image.pdf', 'wb') as cropped_pdf_file:
        cropped_pdf_writer.write(cropped_pdf_file)

# Создаём функцию для преобразования PDF в изображения
def convert_to_images(input_file,):
    images = convert_from_path(input_file)
    image = images[0]
    output_file = "PDF_image.png"
    image.save(output_file, "PNG")

if __name__ == '__main__':
    # Находим путь к PDF
    pdf_path = r'c:/Users/denis/Documents/Denis/Li9/2022-2023L9Cropp.pdf'

    # создаём объект файла PDF
    pdfFileObj = open(pdf_path, 'rb')
    # создаём объект считывателя PDF
    pdfReaded = PyPDF2.PdfReader(pdfFileObj)

    # Создаём словарь для извлечения текста из каждого изображения
    text_per_page = {}
    # Извлекаем страницы из PDF
    for pagenum, page in enumerate(extract_pages(pdf_path, maxpages=400)):   #, page_numbers=[4, 5, 6, 7]
        # pagenum = 4
        # page = 4
        df = pd.DataFrame()
        print('Страница:',  pagenum)

        # Инициализируем переменные, необходимые для извлечения текста со страницы
        pageObj = pdfReaded.pages[pagenum]
        page_text = []
        line_format = []
        text_from_images = []
        text_from_tables = []
        page_content = []
        # Инициализируем количество исследованных таблиц
        table_num = 0
        first_element = True
        table_extraction_flag = False
        # Открываем файл pdf
        pdf = pdfplumber.open(pdf_path)
        # Находим исследуемую страницу
        page_tables = pdf.pages[pagenum]
        # Находим количество таблиц на странице
        tables = page_tables.find_tables()

        # Находим все элементы
        page_elements = [(element.y1, element) for element in page._objs]
        maxElement=len(page_elements)
        # Сортируем все элементы по порядку нахождения на странице
        page_elements.sort(key=lambda a: a[0], reverse=True)

        # Находим элементы, составляющие страницу
        for i, component in enumerate(page_elements):
            # Извлекаем положение верхнего края элемента в PDF
            pos = component[0]
            # Извлекаем элемент структуры страницы
            element = component[1]

            # Проверяем, является ли элемент текстовым
            if isinstance(element, LTTextContainer):
                # Проверяем, находится ли текст в таблице
                if table_extraction_flag == False:
                    # Используем функцию извлечения текста и формата для каждого текстового элемента
                    (line_text, format_per_line) = text_extraction(element)
                    # Добавляем текст каждой строки к тексту страницы
                    page_text.append(line_text)
                    # print(page_text)
                    # Добавляем формат каждой строки, содержащей текст
                    line_format.append(format_per_line)
                    page_content.append(line_text)
                else:
                    # Пропускаем текст, находящийся в таблице
                    pass

            # if isinstance(element, LTFigure):
                # pass
                # Вырезаем изображение из PDF
                # print(element)
                # crop_image(element, pageObj)
                # # Преобразуем обрезанный pdf в изображение
                # convert_to_images('cropped_image.pdf')
                # # Извлекаем текст из изображения
                # image_text = image_to_text('PDF_image.png')
                # text_from_images.append(image_text)
                # page_content.append(image_text)
                # # Добавляем условное обозначение в списки текста и формата
                # page_text.append('image')
                # line_format.append('image')

            # Проверяем элементы на наличие таблиц
            if isinstance(element, LTRect):
                # Если первый прямоугольный элемент
                if first_element == True and (table_num + 1) <= len(tables):
                    # Находим ограничивающий прямоугольник таблицы
                    lower_side = page.bbox[3] - tables[table_num].bbox[3]
                    upper_side = element.y1
                    # Извлекаем информацию из таблицы
                    table = extract_table(pdf_path, pagenum, table_num)
                    # Преобразуем информацию таблицы в формат структурированной строки
                    table_string, df_ = table_converter(table)
                    # print(df_, df_.empty)
                    if not df_.empty:
                        df = pd.concat([df, df_])
                    # Добавляем строку таблицы в список
                    text_from_tables.append(table_string)
                    page_content.append(table_string)
                    # Устанавливаем флаг True, чтобы избежать повторения содержимого
                    table_extraction_flag = True
                    # Преобразуем в другой элемент
                    first_element = False
                    # Добавляем условное обозначение в списки текста и формата
                    page_text.append('table')
                    line_format.append('table')
                # print(i, maxElement)
                # Проверяем, извлекли ли мы уже таблицы из этой страницы
                if element.y0 >= lower_side and element.y1 <= upper_side:
                    pass
                elif (i < maxElement-2):
                    if not isinstance(page_elements[i + 1][1], LTRect):
                        table_extraction_flag = False
                        first_element = True
                        table_num += 1

            # if not df.empty:
            #     print(df.iloc[:, 3:5])
            # Проверяем элементы на наличие изображений
            save_images_from_page(page, 'Page_' + str(pagenum))
            # print(element)
            # if isinstance(element, LTFigure):
            #     print(element)
            #     iw = ImageWriter('cropped')
            #     iw.export_image(element)

        # Создаём ключ для словаря
        dctkey = 'Page_' + str(pagenum)
        if os.path.exists('./cropped/' + dctkey):
            df.to_csv('./cropped/' + dctkey + '/refs.csv', sep=';', encoding='utf-8')
        # Добавляем список списков как значение ключа страницы
        # text_per_page[dctkey] = [page_text, line_format, text_from_images, text_from_tables, page_content]
        text_per_page[dctkey] = [page_text, line_format,  text_from_tables, page_content]


    print(text_per_page)
    # print(df)

    # Закрываем объект файла pdf
    pdfFileObj.close()
