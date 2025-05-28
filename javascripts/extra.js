// 声明一个变量来存储Cursor对象
let CURSOR;

// 定义一个线性插值函数
Math.lerp = (a, b, n) => (1 - n) * a + n * b;

// 定义一个函数来获取元素的样式
const getStyle = (el, attr) => {
    try {
        return window.getComputedStyle
            ? window.getComputedStyle(el)[attr]
            : el.currentStyle[attr];
    } catch (e) {
    }
    return "";
};

// 定义一个Cursor类
class Cursor {
    constructor() {
        // 初始化光标的位置和指针元素的列表
        this.pos = {curr: null, prev: null};
        this.pt = [];
        // 创建光标，初始化事件监听器，开始渲染循环
        this.create();
        this.init();
        this.render();
    }

    // 定义一个方法来移动光标
    move = (left, top) => {
        this.cursor.style["left"] = `${left}px`;
        this.cursor.style["top"] = `${top}px`;
    }

    // 定义一个方法来创建光标
    create = () => {
        if (!this.cursor) {
            this.cursor = document.createElement("div");
            this.cursor.id = "cursor";
            this.cursor.classList.add("hidden");
            document.body.append(this.cursor);
        }

        // 获取所有元素，并将指针元素添加到列表中
        const els = [...document.getElementsByTagName('*')];
        const styles = els.map(el => getStyle(el, "cursor"));
        els.forEach((el, i) => {
            if (styles[i] === "pointer") {
                this.pt.push(el.outerHTML);
            }
        });

        // 创建一个样式元素来改变光标的样式
        document.body.appendChild((this.scr = document.createElement("style")));
        this.scr.innerHTML = `* {cursor: url("/Sakura_embyboss/assets/cursor/default.cur"), auto}`;
    }

    // 定义一个方法来刷新光标
    refresh() {
        this.scr.remove();
        this.cursor.classList.remove("hover");
        this.cursor.classList.remove("active");
        this.pos = {curr: null, prev: null};
        this.pt = [];

        this.create();
        this.init();
        this.render();
    }

    // 定义一个方法来初始化事件监听器
    init() {
        // 当鼠标悬停在指针元素上时，添加一个类
        document.onmouseover = e => this.pt.includes(e.target.outerHTML) && this.cursor.classList.add("hover");
        // 当鼠标离开指针元素时，移除一个类
        document.onmouseout = e => this.pt.includes(e.target.outerHTML) && this.cursor.classList.remove("hover");
        // 当鼠标移动时，移动光标并显示光标
        document.onmousemove = e => {
            (this.pos.curr == null) && this.move(e.clientX - 8, e.clientY - 8);
            this.pos.curr = {x: e.clientX - 8, y: e.clientY - 8};
            this.cursor.classList.remove("hidden");
        };
        // 当鼠标进入窗口时，显示光标
        document.onmouseenter = e => this.cursor.classList.remove("hidden");
        // 当鼠标离开窗口时，隐藏光标
        document.onmouseleave = e => this.cursor.classList.add("hidden");
        // 当鼠标按下时，添加一个类
        document.onmousedown = e => this.cursor.classList.add("active");
        // 当鼠标松开时，移除一个类
        document.onmouseup = e => this.cursor.classList.remove("active");
        // 当用户双击时，改变光标的样式
        document.ondblclick = e => {
            document.body.style.cursor = 'url("assets/cursor/pen.cur"), auto';
        };
    }

    // 定义一个方法来渲染光标
    render() {
        if (this.pos.prev) {
            this.pos.prev.x = Math.lerp(this.pos.prev.x, this.pos.curr.x, 0.15);
            this.pos.prev.y = Math.lerp(this.pos.prev.y, this.pos.curr.y, 0.15);
            this.move(this.pos.prev.x, this.pos.prev.y);
        } else {
            this.pos.prev = this.pos.curr;
        }
        requestAnimationFrame(() => this.render());
    }
}

// 创建一个Cursor对象
(() => {
    CURSOR = new Cursor();
    // 需要重新获取列表时，使用 CURSOR.refresh()
})();
