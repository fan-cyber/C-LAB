#!/bin/bash
export http_proxy="http://192.168.56.1:6087"
export https_proxy="https://192.168.56.1:6087"
rawdic="zh-en-raw.dic"
newdic="zh-en-new.dic"

RED='\033[0;31m'
YELLOW='\033[0;33m'
# No Color
NC='\033[0m'
IFS=''

[[ -e "$newdic" ]] && rm "$newdic"
function TransDisplayName() {
    #$1 zh-CN filename
    #2 fileext
    fileext="$2"
    filedirname=$(dirname "$1")
    filename="$(basename -s -zh-CN${2} $1)"
    if [[ -e "$rawdic" ]] && grep -q "^$filename," "$rawdic";then
        echo "FileName: $filename 使用字典"
        filenameen=$(grep -h "^$filename," "$rawdic"  | head -n 1 | awk -F',' '{print $2}')
    else
        echo "FileName: $filename 使用google"
        filenameen=$(trans zh-CN:en -e google -b "$filename")
        filenameen=$(echo "$filename" | sed 's/\b\(.\)/\u\1/g')
        echo "$filename,$filenameen" >> $newdic
    fi
    filenameen="${filedirname}/${filenameen}-en${fileext}"
    [[ -e "$filenameen" ]] && rm "$filenameen"
    echo "$1"

    #保留前部空格
    # -r保留路径里的\不做特殊字符
    cat "$1" | while read -r line;do
        line=$(echo "$line" | sed 's/\\/\\\\/g')
        if echo "$line" | grep -q 'DisplayName='; then
            displayname=$(echo "$line"  | sed 's/^.\+DisplayName="*\([^,"]\+\)"*,.\+$/\1/')
            if [[ "$displayname" == ".." ]];then
                echo -e "$line" >> "$filenameen"
            elif echo "$displayname" == ".." | grep -q '\$';then
                echo -e "$line" >> "$filenameen"
            else
                if echo $displayname | grep -q '(';then
                    #寻找单位 单位不能被翻译
                    unitstr=$(echo "$displayname" | sed 's/\//\\\//g')
                    unit=$(echo "$unitstr" | sed 's/.\+\((.\+$\)/\1/g')
                    name=$(echo "$unitstr" | sed 's/^\(.\+\)(.\+$/\1/g')
                else
                    name=$displayname
                    unit=""
                fi
                if [[ -e "$rawdic" ]] && grep -q "^$name," "$rawdic";then
                    echo "FileName: $name 使用字典"
                    nameen=$(grep -h "^$name," "$rawdic"  | head -n 1 | awk -F',' '{print $2}')
                else
                    echo "FileName: $name google"
                    nameen=$(trans zh-CN:en -e google -b "$name")
                    #echo -e "${RED}$name Use google translate ${NC} $name -> $nameen"
                    #单词首字母大写
                    nameen=$(echo "$nameen" | sed 's/\b\(.\)/\u\1/g')
                    #echo "$name => $nameen"
                    echo "$name,$nameen" >> $newdic
                fi
                newline=$(echo "$line" | sed "s/$name/$nameen/g")
                echo "$newline" >> "$filenameen"
            fi
        else
            #echo不保留空格
            echo -e "$line" >> "$filenameen"
        fi
    done
    sed -i 's/$//g' "$filenameen"
}

echo "::::::::"
echo "method include file convert"
find ./ -type f -iname "*-zh-CN.inc" | while read filename;do
    TransDisplayName "$filename" ".inc"
done

echo "::::::::"
echo "method file convert"
find "./" -type f -iname "*-zh-CN.mth" | while read filename;do
    TransDisplayName "$filename" ".mth"
done

echo "::::::::"
echo "method back file"
find "./" -type f -iname "*-zh-CN.mbak" | while read filename;do
    TransDisplayName "$filename" ".mbak"
done

echo "::::::::"
echo "Instrument Xml Config"
find "./Instruments/" -type f -iname "*-zh-CN.xml" | while read filename;do
    filenameen=$(echo "$filename" | sed 's/zh-CN/en/')
    [[ -e "$filenameen" ]] && rm "$filenameen"
    echo "$filename -> $filenameen"
    cat "$filename" | while read -r line;do
        line=$(echo "$line" | sed 's/\\/\\\\/g')
        if echo "$line" | grep -q 'DisplayName='; then
            displayname=$(echo "$line"  | sed 's/^.\+DisplayName="\([^"]\+\)" .\+$/\1/')
            if echo "$displayname" | grep -q '^_';then
                newline="$line"
            elif [[ "$displayname" == ".." ]];then
                newline="$line"
            else
                if echo $displayname | grep -q '(';then
                    #寻找单位 单位不能被翻译
                    unitstr=$(echo "$displayname" | sed 's/\//\\\//g')
                    unit=$(echo "$unitstr" | sed 's/.\+\((.\+$\)/\1/g')
                    name=$(echo "$unitstr" | sed 's/^\(.\+\)(.\+$/\1/g')
                else
                    name=$displayname
                    unit=""
                fi
                if [[ -e "$rawdic" ]] && grep -q "^$name," "$rawdic";then
                    nameen=$(grep -h "^$name," "$rawdic" | head -n 1 | awk -F',' '{print $2}')
                else
                    nameen=$(trans zh-CN:en -e google -b "$name")
                    #echo -e "${RED}$name Use google translate ${NC} $name -> $nameen"
                    #单词首字母大写
                    nameen=$(echo "$nameen" | sed 's/\b\(.\)/\u\1/g')
                    echo "$name,$nameen" >> $newdic
                fi
                newline=$(echo -e "$line" | sed "s/$name/$nameen/g")
            fi
        else
            #echo不保留空格
            newline="$line"
        fi
        if echo "$newline" | grep -q 'DisplayClass='; then
            displayname=$(echo "$newline"  | sed 's/^.\+DisplayClass="\([^"]\+\)" .\+$/\1/')
            if [[ -e "$rawdic" ]] && grep -q "^$displayname," "$rawdic";then
                nameen=$(grep -h "^$displayname," "$rawdic"  | head -n 1 | awk -F',' '{print $2}')
            else
                nameen=$(trans zh-CN:en -e google -b "$displayname")
                #echo -e "${RED}$displayname Use google translate ${NC} $displayname -> $nameen"
                #单词首字母大写
                nameen=$(echo "$nameen" | sed 's/\b\(.\)/\u\1/g')
                echo "$displayname,$nameen" >> $newdic
            fi
            newline=$(echo "$newline" | sed "s/$displayname/$nameen/g")
        fi
        echo -e "$newline" >> "$filenameen"
    done
    sed -i 's/$//g' "$filenameen"
done

find "./" -type f -iname "Resource-zh-CN.ini" | while read filename;do
    filenameen=$(echo "$filename" | sed 's/zh-CN/en/')
    [[ -e "$filenameen" ]] && rm "$filenameen"
    echo "$filename -> $filenameen"
    cat "$filename" | while read -r line;do
        name=$(echo "$line"  | awk -F'=' '{print $1}')
        value=$(echo "$line"  | sed "s/^$name=//" | sed 's/$//g')
        if [[ -e "$rawdic" ]] && grep -q "^$value," "$rawdic";then
            valueen=$(grep -h "^$value," "$rawdic" | head -n 1 | awk -F',' '{print $2}')
        else
            valueen=$(trans zh-CN:en -e google -b "$value")
            valueen=$(echo "$valueen" | sed 's/\b\(.\)/\u\1/g')
            echo "$value,$valueen" >> $newdic
        fi
        newline="${name}=${valueen}"
        echo -e "$newline" >> "$filenameen"
    done
    sed -i 's/$//g' "$filenameen"
done

if [[ -e "$newdic" ]];then
    cat "$newdic" | sort | uniq > "$newdic-tmp"
    mv "$newdic-tmp" "$newdic"
fi

zhinen="zhinen.txt"
[[ -e "$zhinen" ]] && rm "$zhinen"
find ./ -type f -iname "*-en.inc" | while read filename;do
    echo "$filename" >> "$zhinen"
    grep -P -h '[\p{Han}]' "$filename" | grep -v '^ *\/\/'>> "$zhinen"
done
echo "" >> "$zhinen"
echo "" >> "$zhinen"

find ./ -type f -iname "*-en.mth" | while read filename;do
    echo "$filename" >> "$zhinen"
    grep -P -h '[\p{Han}]' "$filename" | grep -v '^ *\/\/' | grep -v '^ *\/\*' >> "$zhinen"
done
echo "" >> "$zhinen"
echo "" >> "$zhinen"

find ./ -type f -iname "*-en.mbak" | while read filename;do
    echo "$filename" >> "$zhinen"
    grep -P -h '[\p{Han}]' "$filename" | grep -v '^ *\/\/'>> "$zhinen"
done
echo "" >> "$zhinen"
echo "" >> "$zhinen"
find "./" -type f -iname "*-en.xml" | while read filename;do
    echo "$filename" >> "$zhinen"
    grep -P -h '[\p{Han}]' "$filename" | grep -v '^ *<!--' | grep -v '^ *\/\/' >> "$zhinen"
done
# vim: tw=0 nowrap
