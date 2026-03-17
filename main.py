def main():
    from house_graph.samples import House15Factory, House16Factory, House27Factory
    house15 = House15Factory.build()
    print(f"House 15: {len(house15.nodes)} nodes, {len(house15.edges)} edges")
    house16 = House16Factory.build()
    print(f"House 16: {len(house16.nodes)} nodes, {len(house16.edges)} edges")
    house27 = House27Factory.build()
    print(f"House 27: {len(house27.nodes)} nodes, {len(house27.edges)} edges")


if __name__ == "__main__":
    main()
