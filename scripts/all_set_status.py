input_filename = "biz.txt"
output_filename = "output_commands.txt"

prefix = "python scripts\set_consent.py --business-reg-no "
suffix = " --status opted_in"

with open(input_filename, "r", encoding="utf-8") as infile, open(
    output_filename, "w", encoding="utf-8"
) as outfile:
    for line in infile:
        # 줄 바꿈 및 앞뒤 공백 제거
        biz_no = line.strip()

        # 빈 줄이 아닌 경우에만 처리
        if biz_no:
            # 문자열 조합 후 파일에 쓰기
            command = f"{prefix}{biz_no}{suffix}\n"
            outfile.write(command)

print(f"처리가 완료되었습니다. 결과가 '{output_filename}'에 저장되었습니다.")