# Reflection — Lab 19

**Tên:** _Trần Nguyễn Mỹ Anh_
**Cohort:** _Track 2_
**Path đã chạy:** _lite_

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` /
> `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid
> (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

Trên 50 golden queries, BM25 mạnh nhất ở `exact` (96,7%) vì các thuật ngữ
kỹ thuật xuất hiện nguyên văn. Vector có lợi thế ý nghĩa, nhưng `bge-small-en`
yếu với paraphrase tiếng Việt trong bản Lite (24,0%); đổi sang embedding đa ngữ
như bge-m3 là hướng cải thiện phù hợp. Hybrid RRF thắng tổng thể (78,6% so với
77,8% BM25 và 73,2% vector) và thắng rõ ở `mixed` (100,0%) vì giữ được cả
signal keyword lẫn semantic. Tôi không dùng hybrid khi cần exact-match có tính
quy định (mã lỗi, tên SKU, trích dẫn pháp lý) — BM25/rule filter dễ giải thích,
rẻ hơn và chính xác hơn. Tôi cũng chọn pure vector khi corpus nhỏ, query hoàn
toàn diễn đạt lại, latency/cost của hai retriever không chấp nhận được, và đã
đo bằng multilingual embedding phù hợp.

---

## Điều ngạc nhiên nhất khi làm lab này

P99 server-side khác rất xa P99 wall-clock: tối ưu retrieval không thay thế
được việc quan sát cả mạng lẫn cold-start.

---

## Bonus challenge

- [x] Đã làm bonus (xem `bonus/`)
- [ ] Pair work với: _<tên đồng đội nếu có>_
