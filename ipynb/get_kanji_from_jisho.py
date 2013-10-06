# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 13:01:24 2013

@author: FL232714
"""
import urllib2
import xml.etree.cElementTree as ET

def get_related_kanji(kanji):
    url = "http://jisho.org/words?jap=*%s*&eng=&dict=edict&tag=&sortorder=relevance" % (kanji)
    data = urllib2.urlopen(url).read()
    
    data = data.split('\n')
    
    trigger = False
    table_data = []
    for row in data:
        if trigger:
            table_data.append(row)
            if row.find("</table>") != -1:
                trigger = False
        if row.find("<!-- Found words -->") != -1:
            trigger = True
    with file('test_data.html', 'w') as f:
        f.writelines("\n".join(table_data))
    return table_data
    
def get_test_data():
    tree = ET.ElementTree(file='test.xml')
    output = []
    for elem in tree.iter(tag='td'):
        print elem.tag, elem.attrib
        if 'class' in elem.attrib:
            if elem.attrib['class'] == 'kanji_column':
                print elem[0].tag, elem[0].attrib, elem[0].text.encode('utf-8')
                print elem[0][0].tag, elem[0][0].attrib, elem[0][0].text.encode('utf-8')
                output.append(elem[0].text.strip() + elem[0][0].text.strip())
            else:
                print (elem.text).encode('utf-8')
                output.append(elem.text.strip())
    return output
    
if __name__ == '__main__':
    try:
        data
    except:
        data = get_related_kanji(unicode("車"))
    test_data = get_test_data()