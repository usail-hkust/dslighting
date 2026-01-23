from dotenv import load_dotenv
load_dotenv()

import dslighting


def run_processing(data_path: str):
    return dslighting.process(data_path, "清洗并生成标准数据集")


def run_analysis(data_path: str):
    return dslighting.analyze(data_path, "做可视化和分析", max_iterations=3)


def run_modeling(data_path: str):
    return dslighting.model(data_path, "做一个预测模型")

def print_summary(result, title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(f"Success: {result.success}")
    print(f"Score: {result.score}")
    print(f"Cost: ${result.cost:.4f}")
    print(f"Duration: {result.duration:.2f}s")

    summary = result.summary or {}
    preview = summary.get("preview")
    if preview:
        print("\n[Preview]")
        print(preview)

    images = summary.get("images", [])
    if images:
        print("\n[Images]")
        for path in images[:10]:
            print(f"- {path}")

    artifacts = summary.get("artifacts", [])
    if artifacts:
        print("\n[Artifacts]")
        for item in artifacts[:10]:
            print(f"- {item['path']}")


def main():
    data_path = "./data/raw"

    # result_processing = run_processing(data_path)
    # print_summary(result_processing, "Open-Ended Processing")

    result_analysis = run_analysis(data_path)
    print_summary(result_analysis, "Open-Ended Analysis")

    # result_modeling = run_modeling(data_path)
    # print_summary(result_modeling, "Open-Ended Modeling")


if __name__ == "__main__":
    main()
