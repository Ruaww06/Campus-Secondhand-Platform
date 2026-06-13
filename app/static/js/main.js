/* ============================================
   校园二手交易平台 - 全局 JavaScript
   ============================================ */

// ---------- CSRF Token 获取 ----------
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
}

// ---------- AJAX POST JSON ----------
function postJSON(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    }).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    });
}

// ---------- Toast 提示 ----------
function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type}`;

    const iconMap = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    toast.innerHTML = `<span>${iconMap[type] || iconMap.info}</span><span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-hiding');
        toast.addEventListener('animationend', () => toast.remove());
    }, 3000);
}

// ---------- 确认对话框 ----------
function confirmAction(message, onConfirm) {
    let modalEl = document.getElementById('globalConfirmModal');
    if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.className = 'modal fade';
        modalEl.id = 'globalConfirmModal';
        modalEl.tabIndex = -1;
        modalEl.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">确认操作</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p id="globalConfirmMessage"></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-danger" id="globalConfirmBtn">确认</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modalEl);
    }

    document.getElementById('globalConfirmMessage').textContent = message;
    const modal = new bootstrap.Modal(modalEl);

    const confirmBtn = document.getElementById('globalConfirmBtn');
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    newConfirmBtn.addEventListener('click', () => {
        modal.hide();
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    });

    modal.show();
}

// ---------- 收藏按钮切换 ----------
function toggleFavorite(button) {
    const goodsId = button.dataset.goodsId;
    const isFavorited = button.classList.contains('favorited');
    const url = isFavorited ? '/favorite/remove' : '/favorite/add';

    button.disabled = true;
    const originalHTML = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>处理中...';

    const formData = new FormData();
    formData.append('goods_id', goodsId);

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            button.classList.toggle('favorited');
            const icon = button.querySelector('.favorite-icon');
            if (icon) {
                icon.innerHTML = isFavorited ? '&#9825; 收藏' : '&#9829; 已收藏';
            }
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(() => showToast('网络错误，请稍后重试', 'error'))
    .finally(() => {
        button.disabled = false;
        button.innerHTML = originalHTML;
    });
}

// ---------- 星星评分初始化 ----------
function initStarRating(container) {
    if (!container) return;
    const stars = container.querySelectorAll('.star');
    const input = container.querySelector('input[type="hidden"]');
    let currentValue = parseInt(input?.value) || 0;

    function updateStars(value) {
        stars.forEach((star, index) => {
            star.classList.toggle('active', index < value);
        });
    }

    stars.forEach((star, index) => {
        star.addEventListener('mouseenter', () => updateStars(index + 1));
        star.addEventListener('mouseleave', () => updateStars(currentValue));
        star.addEventListener('click', () => {
            currentValue = index + 1;
            if (input) input.value = currentValue;
            updateStars(currentValue);
        });
    });

    updateStars(currentValue);
}

// ---------- 图片上传预览 ----------
function initImagePreview(inputElement, previewContainer) {
    if (!inputElement || !previewContainer) return;

    inputElement.addEventListener('change', function () {
        previewContainer.innerHTML = '';
        const files = Array.from(this.files);

        files.forEach(file => {
            if (!file.type.startsWith('image/')) return;

            const reader = new FileReader();
            reader.onload = (e) => {
                const wrapper = document.createElement('div');
                wrapper.className = 'preview-item';
                wrapper.innerHTML = `
                    <img src="${e.target.result}" alt="预览">
                    <button type="button" class="preview-remove">&times;</button>
                `;
                wrapper.querySelector('.preview-remove').addEventListener('click', () => {
                    wrapper.remove();
                });
                previewContainer.appendChild(wrapper);
            };
            reader.readAsDataURL(file);
        });
    });
}

// ---------- 表单提交增强（防重复提交） ----------
function initFormSubmit(formElement) {
    if (!formElement) return;

    formElement.addEventListener('submit', function (e) {
        const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
        if (!submitBtn) return;

        if (submitBtn.disabled) {
            e.preventDefault();
            return;
        }

        submitBtn.disabled = true;
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>提交中...';

        // 如果表单验证失败（HTML5），恢复按钮状态
        setTimeout(() => {
            if (!this.checkValidity || this.checkValidity()) return;
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }, 0);

        // 页面 unload 时不需要恢复，正常提交后页面会跳转
    });
}

// ---------- 图片管理 (A12) ----------
function deleteImage(button) {
    const card = button.closest('.image-card');
    const imageId = card.dataset.imageId;
    const container = card.closest('[data-goods-id]');
    const goodsId = container.dataset.goodsId;

    confirmAction('确定要删除这张图片吗？', () => {
        postJSON('/' + goodsId + '/images/delete', { image_id: parseInt(imageId) })
            .then(data => {
                if (data.success) {
                    card.remove();
                    showToast('图片已删除', 'success');
                    const remaining = container.querySelectorAll('.image-card');
                    if (remaining.length > 0 && !container.querySelector('.btn-set-main[disabled]')) {
                        const firstBtn = remaining[0].querySelector('.btn-set-main');
                        const firstInner = remaining[0].querySelector('.image-card-inner');
                        if (firstBtn) firstBtn.disabled = true;
                        if (firstBtn) firstBtn.textContent = '封面';
                        if (firstInner) firstInner.style.borderColor = 'var(--color-primary)';
                    }
                } else {
                    showToast(data.message || '删除失败', 'error');
                }
            })
            .catch(() => showToast('网络错误', 'error'));
    });
}

function setMainImage(button) {
    const card = button.closest('.image-card');
    if (button.disabled) return;
    const imageId = card.dataset.imageId;
    const container = card.closest('[data-goods-id]');
    const goodsId = container.dataset.goodsId;

    postJSON('/' + goodsId + '/images/set_main', { image_id: parseInt(imageId) })
        .then(data => {
            if (data.success) {
                container.querySelectorAll('.image-card').forEach(c => {
                    const inner = c.querySelector('.image-card-inner');
                    const btn = c.querySelector('.btn-set-main');
                    if (inner) inner.style.borderColor = 'var(--border-color, #dee2e6)';
                    if (btn) { btn.disabled = false; btn.textContent = '设为封面'; }
                });
                const inner = card.querySelector('.image-card-inner');
                if (inner) inner.style.borderColor = 'var(--color-primary)';
                button.disabled = true;
                button.textContent = '封面';
                showToast('已设为主图', 'success');
            } else {
                showToast(data.message || '设置失败', 'error');
            }
        })
        .catch(() => showToast('网络错误', 'error'));
}

function moveImage(card, direction) {
    const container = card.closest('[data-goods-id]');
    const goodsId = container.dataset.goodsId;
    const cards = Array.from(container.querySelectorAll('.image-card'));
    const idx = cards.indexOf(card);
    const targetIdx = idx + direction;
    if (targetIdx < 0 || targetIdx >= cards.length) return;

    if (direction === -1) {
        container.insertBefore(card, cards[targetIdx]);
    } else {
        container.insertBefore(cards[targetIdx + 1], card);
    }

    const orderedIds = Array.from(container.querySelectorAll('.image-card'))
        .map(c => parseInt(c.dataset.imageId));
    postJSON('/' + goodsId + '/images/reorder', { image_ids: orderedIds })
        .then(data => {
            if (data.success) showToast('排序已更新', 'success');
            else showToast(data.message || '排序更新失败', 'error');
        })
        .catch(() => showToast('网络错误', 'error'));
}

function uploadNewImages() {
    const input = document.getElementById('addImagesInput');
    const container = document.querySelector('[data-goods-id]');
    if (!input || !container) return;
    const goodsId = container.dataset.goodsId;
    const files = input.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) formData.append('images', files[i]);

    const btn = document.getElementById('btnUploadImages');
    btn.disabled = true;
    const origText = btn.textContent;
    btn.textContent = '上传中...';

    fetch('/' + goodsId + '/images/add', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast('成功上传 ' + data.count + ' 张图片', 'success');
            setTimeout(() => location.reload(), 800);
        } else {
            showToast(data.message || '上传失败', 'error');
        }
    })
    .catch(() => showToast('网络错误', 'error'))
    .finally(() => {
        btn.disabled = false;
        btn.textContent = origText;
    });
}

// ---------- 页面加载后自动初始化 ----------
document.addEventListener('DOMContentLoaded', () => {
    // 自动初始化所有带 data-confirm 的链接
    document.querySelectorAll('a[data-confirm]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            confirmAction(link.dataset.confirm, () => {
                window.location.href = link.href;
            });
        });
    });

    // 支持 data-confirm 在表单上
    document.querySelectorAll('form[data-confirm]').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
            confirmAction(this.dataset.confirm, () => {
                if (submitBtn && this.hasAttribute('data-prevent-double-submit')) {
                    HTMLFormElement.prototype.submit.call(this);
                } else {
                    this.submit();
                }
            });
        });
    });

    // 自动初始化所有带 data-toggle-favorite 的按钮
    document.querySelectorAll('[data-toggle-favorite]').forEach(btn => {
        btn.addEventListener('click', () => toggleFavorite(btn));
    });

    // 自动初始化所有 .star-rating 容器
    document.querySelectorAll('.star-rating').forEach(container => {
        initStarRating(container);
    });

    // 自动初始化所有带 data-preview 的图片上传
    document.querySelectorAll('input[data-preview]').forEach(input => {
        const target = document.querySelector(input.dataset.preview);
        initImagePreview(input, target);
    });

    // 自动初始化所有带 data-prevent-double-submit 的表单
    document.querySelectorAll('form[data-prevent-double-submit]').forEach(form => {
        initFormSubmit(form);
    });

    // --- A12: 图片管理事件委托 ---

    // 删除图片 / 设为封面
    document.addEventListener('click', function(e) {
        const delBtn = e.target.closest('.btn-delete-image');
        if (delBtn) { e.preventDefault(); deleteImage(delBtn); return; }

        const setMainBtn = e.target.closest('.btn-set-main');
        if (setMainBtn) { e.preventDefault(); setMainImage(setMainBtn); return; }

        const uploadBtn = e.target.closest('#btnUploadImages');
        if (uploadBtn) { e.preventDefault(); uploadNewImages(); return; }
    });

    // 排序手柄：点击上移，Shift+点击下移
    document.addEventListener('click', function(e) {
        const handle = e.target.closest('.sort-handle');
        if (handle) {
            const card = handle.closest('.image-card');
            const direction = e.shiftKey ? 1 : -1;
            moveImage(card, direction);
        }
    });

    // 添加图片输入预览
    const addImagesInput = document.getElementById('addImagesInput');
    if (addImagesInput) {
        addImagesInput.addEventListener('change', function() {
            const btn = document.getElementById('btnUploadImages');
            if (btn) btn.disabled = this.files.length === 0;
            const preview = document.getElementById('addImagesPreview');
            if (preview) {
                preview.innerHTML = '';
                Array.from(this.files).forEach(file => {
                    if (!file.type.startsWith('image/')) return;
                    const reader = new FileReader();
                    reader.onload = e => {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.style.cssText = 'width:80px;height:60px;object-fit:cover;border-radius:4px;';
                        preview.appendChild(img);
                    };
                    reader.readAsDataURL(file);
                });
            }
        });
    }
});
