# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 15:00:59 2013

@author: FL232714
"""
import sys
from PyQt4 import QtCore, QtGui, uic
import xml.etree.cElementTree as ET

try:
    from PyQt4.QtCore import QString
except ImportError:
    # we are using Python3 so QString is not defined
    QtCore.QString = type("")

#==============================================================================
# helper functions
#==============================================================================

def model_data_to_string(data):
    if isinstance(data, QtCore.QVariant):
        return data.toString()
    else:
        return data

#==============================================================================
# Classes
#==============================================================================

class KanjiDB(object):
    """ kanji database class that loads up by parsing the kanjidic2 dictionary 
    file and can then be used for lookup of specific kanji.
    """
    def __init__(self, filename='kanjidic2.xml'):
        self.tree = ET.ElementTree(file=filename)
        literals = self.tree.getroot().findall('character/literal')
        self.literals = [literal.text for literal in literals]
        
    def getKanjiDetails(self, kanji):
        """returns the kanji, kana and the meanings from dictionary 
        for a given kanji"""
        element = self.tree.getroot()[self.literals.index(kanji) + 1]
        kanji = element.find('literal').text
        kana = [elem.text for elem in filter(
                lambda reading: reading.attrib['r_type'] in ['ja_on', 'ja_kun'], 
                            element.findall('reading_meaning/rmgroup/reading'))]
        meanings = [elem.text for elem in filter(
                lambda elem: elem.attrib == {}, element.findall(
                                    'reading_meaning/rmgroup/meaning'))]
        return (kanji, kana, meanings)
        
    def getFormattedKanjiDetails(self, kanji):
        (kanji, kana, meanings) = self.getKanjiDetails(kanji)
        return """<b>%s</b> / %s / %s""" % (kanji,
                                            ", ".join(kana),
                                             ", ".join(meanings))
    
    def isInDB(self, kanji):
        return kanji in self.literals

class DictionaryDB(object):
    def __init__(self, filename='JMdict.xml'):
        self.tree = ET.ElementTree(file=filename)
        self.word_entries = self.tree.getroot().findall('entry/k_ele/keb')
        self.words = [entry.text for entry in self.word_entries]
        self.commonness_dict = self.generateCommonnessDict()
    
    def findWordsContainingExpression(self, kanji_expression):
        return filter(lambda expression: kanji_expression in expression, 
                      self.words)

    def isCommonWord(self, word):
        found = False
        for elem in self.tree.findall('entry/k_ele'):
            if elem.find('keb').text == word:
                found = True
                break
        if found:
            if elem.find('ke_pri') != None:
                return True
            else:
                return False
        else:
            return False
    
    def generateCommonnessDict(self):
        commonness_list = []
        for elem in self.tree.findall('entry/k_ele'):
            if elem.find('ke_pri') != None:
                commonness_list.append(True)
            else:
                commonness_list.append(False)
        return dict(zip(self.words, commonness_list))
        
    def areCommonWordsTraversingMethod(self, word_list):
        """returns a boolean list telling if a given word in a word list
        is common while traversing the dictionary tree only once """
        found = [False for word in word_list]
        for elem in self.tree.findall('entry/k_ele'):
            if elem.find('keb').text in word_list:
                if elem.find('ke_pri') != None:
                    found[word_list.index(elem.find('keb').text)] = True
        return found
    
    def areCommonWords(self, word_list):
        """returns a boolean list telling if a given word in a word list
        is common while looking up the word in a pre-generated dictionary"""
        return [self.commonness_dict[word] for word in word_list]
    
    def getDefinition(self, kanji_expression):
        kanji_expression = unicode(kanji_expression) 
        for elem in self.tree.findall('entry'):
            search = elem.find('k_ele/keb')
            if search != None:
                if search.text == kanji_expression:
                    reading = elem.find('r_ele/reb').text
                    senses = elem.findall('sense/gloss')
                    senses = filter(
                        lambda item: item.attrib.items()[0][1] == 'eng', senses)
                    senses = [sense.text for sense in senses]
                    return (reading, senses)
                
class DictionaryWord(object):
    def __init__(self, word, is_common=False):
        self.word = word
        self.is_common = is_common
        
    def display_word_with_commonness(self):
        if self.is_common:
            return self.word + "[Common]"
        else:
            return self.word + "[Uncommon]"

#==============================================================================
# Main window
#==============================================================================

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        # load the UI
        self.ui = uic.loadUi("main_window.ui", self)

        # init class data
        self.initData()
        
        # customize the UI
        self.initUI()
        
        # connect slots
        self.connectSlots()
        
    def initUI(self):
        self.ui.listView.setModel(self.history_model)
        self.ui.listView_2.setModel(self.current_words_model)
        
    def initData(self):
        self.dict_db = DictionaryDB()
        self.kanji_db = KanjiDB()
        self.current_words = []
        self.current_words_model = QtGui.QStringListModel()
        self.history = []
        self.history_model = QtGui.QStringListModel()
        
    def connectSlots(self):
        QtCore.QObject.connect(self.ui.pushButton,
                               QtCore.SIGNAL('clicked()'),
                                self.searchForKanjiExpression)

        QtCore.QObject.connect(self.ui.checkBox,
                               QtCore.SIGNAL('stateChanged(int)'),
                                self.updateCurrentWordsListView)
                                
        QtCore.QObject.connect(self.ui.listView,
                               QtCore.SIGNAL('clicked(QModelIndex)'),
                                self.updateFollowingHistorySelection)
        
        QtCore.QObject.connect(self.ui.listView_2,
                               QtCore.SIGNAL('clicked(QModelIndex)'),
                                self.updateGuiFollowingSelection)
        
        QtCore.QObject.connect(self.ui.listView_2,
                               QtCore.SIGNAL('doubleClicked(QModelIndex)'),
                                self.copyExpressionToSearchBox)
                                    
    def searchForKanjiExpression(self, append_to_history=True):
        kanji_expression = unicode(self.ui.lineEdit.text())
        if append_to_history:        
            self.addExpressionToHistory(kanji_expression)
            self.updateHistoryListView()
        self.updateTatoebaPage(kanji_expression)
        self.updateGuiWithExpression(kanji_expression)
        filtered_words = self.dict_db.findWordsContainingExpression(kanji_expression)
        commonness = self.dict_db.areCommonWords(filtered_words)
        self.current_words = []
        for item in zip(filtered_words, commonness):
            self.current_words.append(DictionaryWord(item[0], item[1])) 
        self.updateCurrentWordsListView()
        
    def addExpressionToHistory(self, expression):
        self.history.append(expression)
      
    def updateHistoryListView(self):
        self.history_model.setStringList([word for word in self.history])
    
    def updateCurrentWordsListView(self):
        if self.ui.checkBox.isChecked():
            display_list = [dict_word.display_word_with_commonness() for dict_word in self.current_words if dict_word.is_common]
        else:
            display_list = [dict_word.display_word_with_commonness() for dict_word in self.current_words]
            
        self.current_words_model.setStringList(display_list)

    def updateTatoebaPage(self, expression):
        adr = u"http://tatoeba.org/fre/sentences/search?query=%s&from=jpn&to=eng" % expression
        url = QtCore.QUrl(adr)
        self.webView.load(url)
    
    def updateKanjiTextBrowser(self, expression):
        display_html = ""
        for character in expression:
            if self.kanji_db.isInDB(character):
                display_html += self.kanji_db.getFormattedKanjiDetails(character) + "<br>"
        self.ui.textBrowser_2.setText(display_html)
            
    
    def updateDictionaryDefinition(self, expression):
        definition = self.dict_db.getDefinition(expression)
        if definition != None:
            (reading, senses) = definition
        else:
            (reading, senses) = ("", "")
        display_html = u"""
        <b>%s</b>
        <e>[%s]</e><br/>
        %s
        """ % (expression, reading, ", ".join(senses))
        self.ui.textBrowser.setText(display_html)
     
    def copyExpressionToSearchBox(self, index):
        expression = model_data_to_string(
                    self.current_words_model.data(index, 0)).split('[')[0]
        self.ui.lineEdit.setText(expression)
        self.searchForKanjiExpression()
    
    def updateGuiFollowingSelection(self, index):
        expression = model_data_to_string(
                    self.current_words_model.data(index, 0)).split('[')[0]
        expression = unicode(expression)
        self.updateGuiWithExpression(expression)
    
    def updateGuiWithExpression(self, expression):
        self.updateDictionaryDefinition(expression)
        self.updateKanjiTextBrowser(expression)
        self.updateTatoebaPage(expression)
    
    def updateFollowingHistorySelection(self, index):
        expression = model_data_to_string(
                    self.history_model.data(index, 0))
        self.ui.lineEdit.setText(expression)
        self.searchForKanjiExpression(append_to_history=False)
        
    def closeEvent(self, e):
        pass
    
    
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())