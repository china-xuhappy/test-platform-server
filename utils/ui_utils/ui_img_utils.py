# import cv2, base64
#
#
# def cv2_sign(image_url, first_point, last_point):
#     """
#     根据坐标标记图片
#     :param image_url: 图片路径
#     :param first_point: 开始坐标
#     :param last_point: 结束坐标
#     :return:
#     """
#     image = cv2.imread(image_url)
#     # print("shape", image.shape)
#     # print("type:", type(image))
#     # first_point = (60, 603)
#     # last_point = (452, 671)
#     cv2.rectangle(image, first_point, last_point, (0, 0, 255), 2)
#     return image
#
#
# def cv2_base64(image):
#     """
#     cv2图片 转 base64 --- 主要用于前端显示
#     :param image: 图片
#     :return:
#     """
#     base64_str = cv2.imencode('.jpg', image)[1].tostring()
#     base64_str = base64.b64encode(base64_str)
#     return base64_str
#
#
# # print(cv2_base64(cv2.imread("home1.png")))
