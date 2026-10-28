"""CLI: python -m qcm [ingest|build|index|ask|sql|eval|all]"""
import argparse
import json

from . import agent, evaluate, ingest, rag, tools, warehouse


def main() -> None:
    p = argparse.ArgumentParser(prog="qcm")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest")
    sub.add_parser("build")
    sub.add_parser("index")
    sub.add_parser("all", help="ingest + build + index")
    a = sub.add_parser("ask")
    a.add_argument("pergunta")
    a.add_argument("-v", "--verbose", action="store_true")
    s = sub.add_parser("sql")
    s.add_argument("query")
    e = sub.add_parser("eval")
    e.add_argument("-k", type=int, default=3)
    args = p.parse_args()

    if args.cmd in ("ingest", "all"):
        for linha in ingest.run():
            print("ingest:", linha)
    if args.cmd in ("build", "all"):
        warehouse.build()
        print("build: warehouse ok")
    if args.cmd in ("index", "all"):
        n, nome = rag.index()
        print(f"index: {n} chunks com {nome}")
    if args.cmd == "ask":
        print(agent.ask(args.pergunta, verbose=args.verbose))
    if args.cmd == "sql":
        print(tools.consultar_sql(args.query))
    if args.cmd == "eval":
        r = evaluate.run(args.k)
        print(json.dumps({k: v for k, v in r.items() if k != "detalhes"}, ensure_ascii=False))
        for d in r["detalhes"]:
            if not d["ok"]:
                print("  falhou:", d["pergunta"], "->", d["top"])


if __name__ == "__main__":
    main()
