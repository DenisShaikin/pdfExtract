from translate import Translator

translator = Translator(from_lang='zh-cn', to_lang='ru')
print(translator.translate('零件号码'))