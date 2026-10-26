<template>
    <div id='text_file_select' :class="{ 'tx-slim': slim }">
        <label v-if="!slim" for="textArea">{{ $t('message.text') }}:</label>
        <textarea id="textArea" class="form-control" v-model="text" @input="handleManualInput"
            :placeholder="$t('message.enterText')"></textarea>

        <template v-if="!slim">
            <label for="textFileInput">{{ $t('message.orUploadDocument') }}:</label>
            <div class="file_select_container">
                <button @click="triggerTextFileInput" class="mx-auto">{{ $t('message.chooseFile') }}</button>
                <span class="border p-2 text-primary " v-if="selectedTextFileName">{{ selectedTextFileName }}</span>
            </div>
        </template>

        <input type="file" ref="textFileInput" @change="uploadFile" id="textFileInput"
            accept=".doc,.docx,.pdf,.txt,.rtf" style="display: none;" />

        <div v-if="isLoading" class="loader">{{ $t('message.loading') }}...</div>
    </div>
</template>


<script>
export default {
    name: 'TextInput',
    props: {
        slim: { type: Boolean, default: false },
    },
    emits: ['childEvent', 'file-uploaded', 'manual-input'],

    data() {
        return {
            text: '',
            isLoading: false,
            selectedTextFileName: '',
        }
    },
    //当输入框的值发生变化时，通知HomeView更新text_handwriting 7.4
    watch: {
        text: function (val) {
            this.$emit('childEvent', val);
        }
    },
    created() {
        const localStorageItems = ['selectedTextFileName','text']
        localStorageItems.forEach(item => {
            const value = localStorage.getItem(item);
            if (value !== null && value !== "undefined") {
                this[item] = JSON.parse(value);
            } else {
                console.log('localstorage缺失item:' + item)
            }
        });
    },
    methods: {
        handleManualInput() {
            this.$emit('manual-input');
        },
        replaceText(value) {
            this.text = typeof value === 'string' ? value : '';
            localStorage.setItem('text', JSON.stringify(this.text));
        },
        uploadFile(e) {
            let file = e.target.files[0];
            // 当用户选择了一个新的文本文件时，更新 selectedTextFileName
            this.selectedTextFileName = e.target.files[0].name;
            // localStorage.setItem('textFile', JSON.stringify(this.textFile));
            localStorage.setItem('selectedTextFileName', JSON.stringify(this.selectedTextFileName));

            let formData = new FormData();

            formData.append('file', file);  // 'file' 是你在服务器端获取文件数据时的 key
            this.isLoading = true;
            this.$http.post(
                '/api/textfileprocess',
                formData, {

                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
                .then(response => {
                    this.text = response.data.text;
                    this.$emit('childEvent', this.text);
                    this.$emit('file-uploaded', this.selectedTextFileName);
                    localStorage.setItem('text', JSON.stringify(this.text));
                    this.isLoading = false;
                })
                .catch(error => {
                    console.error(error);
                    this.isLoading = false;
                });
        },
        triggerTextFileInput() {
            this.$refs.textFileInput.click();
        },
    },

}
</script>

<style scoped>
#text_file_select {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 10px;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
}

#text_file_select #textArea {
    flex: 1 1 auto;
    min-height: 0;
    resize: none;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC",
        "Microsoft YaHei", sans-serif;
    font-size: 14px;
    line-height: 1.6;
}

#text_file_select.tx-slim {
    gap: 0;
}

#text_file_select.tx-slim #textArea {
    height: 100%;
    border: none;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
    padding: 0;
    outline: none;
}

#text_file_select.tx-slim #textArea:focus {
    box-shadow: none;
    background: transparent;
}


#text_file_select label {
    font-size: 1.1rem;
    font-weight: 500;
}

#text_file_select span {
    display: block;
    margin-left: 10px;
    margin-top: 5px;
    font-size: 0.9rem;
    color: #444;
}

.file_select_container {
    display: flex;
    /* gap: 10px; */
    align-items: center;
}

.file_select_container button {
    padding: 10px 10px;
    font-size: 0.9rem;
    color: white;
    background-color: #4285f4;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}

.file_select_container button:disabled {
    background-color: grey;
}

.file_select_container span{
    font-size: 0.9rem;
}

.loader {
    border: 16px solid #f3f3f3;
    /* Light grey */
    border-top: 16px solid #3498db;
    /* Blue */
    border-radius: 50%;
    width: 120px;
    height: 120px;
    animation: spin 2s linear infinite;
    position: absolute;
    /* 设置动画为绝对定位 */
    top: 50%;
    /* 将动画定位在父元素的中心 */
    left: 50%;
    transform: translate(-50%, -50%);
    /* 用 transform 属性将动画元素的中心对准父元素的中心 */
}

#textarea {
    width: 100%;
    height: 200px;
    padding: 12px 20px;
    box-sizing: border-box;
    border: 2px solid #ccc;
    border-radius: 4px;
    background-color: #f8f8f8;
    font-size: 16px;
    transition: all 0.3s ease-in-out;
}

#textarea:hover {
    border: 2px solid #4285f4;
    background-color: #fff;
    box-shadow: 0 0 5px #4285f4;
    transform: scale(1.05);

}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}
</style >
